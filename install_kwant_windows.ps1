#Requires -Version 5.1
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
<#
.SYNOPSIS
    Installs Kwant 1.5 on Windows and wires it up for VS Code, PowerShell and cmd.exe.

.DESCRIPTION
    Kwant has compiled extensions and needs MUMPS for good performance, so pip is a bad
    route on Windows. conda-forge publishes win-64 builds of kwant 1.5.0 and of
    python-mumps, which is what this script uses.

    Steps:
      1. Find conda. If absent, download and silently install Miniforge3 (conda-forge's
         own minimal distribution -- no Anaconda licence concerns).
      2. Create a dedicated environment with Kwant and the full notebook stack.
      3. Install optional extras (MUMPS solver, sympy, qsymm, plotly) best-effort, so
         one unavailable package cannot fail the whole install.
      4. Register a Jupyter kernel named "Python (kwant)" so VS Code and JupyterLab see it.
      5. Run `conda init` for both PowerShell and cmd.exe.
      6. Verify with a real transport calculation.

.PARAMETER EnvName
    Name of the conda environment to create. Default: kwant

.PARAMETER PythonVer
    Python version. Default: 3.13 (conda-forge has a win-64 kwant 1.5.0 build for it).

.PARAMETER Force
    Remove and recreate the environment if it already exists.

.PARAMETER SkipInit
    Do not run `conda init`. Use if you manage your own shell profiles.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\install_kwant_windows.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\install_kwant_windows.ps1 -Force -PythonVer 3.11
#>

[CmdletBinding()]
param(
    [string]$EnvName   = 'kwant',
    [string]$PythonVer = '3.13',
    [switch]$Force,
    [switch]$SkipInit
)

$ErrorActionPreference = 'Stop'
$ProgressPreference    = 'SilentlyContinue'   # makes Invoke-WebRequest much faster

# ---------------------------------------------------------------- helpers
$script:StepNo = 0
function Write-Step {
    param([string]$Message)
    $script:StepNo++
    Write-Host ''
    Write-Host ("[{0}] {1}" -f $script:StepNo, $Message) -ForegroundColor Cyan
    Write-Host ('-' * 70) -ForegroundColor DarkGray
}
function Write-Ok   { param([string]$m) Write-Host "    OK   $m" -ForegroundColor Green }
function Write-Warn { param([string]$m) Write-Host "    WARN $m" -ForegroundColor Yellow }
function Write-Info { param([string]$m) Write-Host "         $m" -ForegroundColor Gray }

function Invoke-Conda {
    <# Runs conda and streams output. Throws on non-zero exit.
       NB: the parameter must NOT be called $Args -- that shadows PowerShell's
       automatic $args variable and breaks splatting. #>
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$CondaArgs)
    & $script:CondaExe @CondaArgs
    if ($LASTEXITCODE -ne 0) {
        throw "conda exited with code $LASTEXITCODE :  conda $($CondaArgs -join ' ')"
    }
}

function Invoke-CondaSafe {
    <# Same, but returns $false instead of throwing. For optional packages. #>
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$CondaArgs)
    & $script:CondaExe @CondaArgs
    return ($LASTEXITCODE -eq 0)
}

Write-Host ''
Write-Host '===============================================================' -ForegroundColor White
Write-Host '  Kwant 1.5 installer for Windows' -ForegroundColor White
Write-Host '===============================================================' -ForegroundColor White
Write-Info "environment : $EnvName"
Write-Info "python      : $PythonVer"

# ---------------------------------------------------------------- 1. locate conda
Write-Step 'Locating conda'

$script:CondaExe = $null

$cmd = Get-Command conda -ErrorAction SilentlyContinue
if ($cmd) {
    # Prefer the real executable over the shell shim
    $candidate = Join-Path (Split-Path (Split-Path $cmd.Source -Parent) -Parent) 'Scripts\conda.exe'
    $script:CondaExe = if (Test-Path $candidate) { $candidate } else { $cmd.Source }
    Write-Ok "found on PATH: $script:CondaExe"
}
else {
    $roots = @(
        (Join-Path $HOME 'miniforge3'),
        (Join-Path $HOME 'mambaforge'),
        (Join-Path $HOME 'miniconda3'),
        (Join-Path $HOME 'anaconda3'),
        'C:\ProgramData\miniforge3',
        'C:\ProgramData\miniconda3',
        'C:\ProgramData\Anaconda3'
    )
    foreach ($r in $roots) {
        $p = Join-Path $r 'Scripts\conda.exe'
        if (Test-Path $p) { $script:CondaExe = $p; Write-Ok "found: $p"; break }
    }
}

# ---------------------------------------------------------------- 2. install Miniforge
if (-not $script:CondaExe) {
    Write-Warn 'conda not found -- installing Miniforge3 (this takes a few minutes)'

    $installDir = Join-Path $HOME 'miniforge3'
    if ($installDir -match '\s') {
        throw "Install path '$installDir' contains a space; the NSIS installer cannot handle that. Install Miniforge manually."
    }

    $url = 'https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Windows-x86_64.exe'
    $exe = Join-Path $env:TEMP 'Miniforge3-Windows-x86_64.exe'

    Write-Info "downloading $url"
    Invoke-WebRequest -Uri $url -OutFile $exe -UseBasicParsing
    Write-Ok ("downloaded {0:N1} MB" -f ((Get-Item $exe).Length / 1MB))

    Write-Info "installing to $installDir (silent)"
    # NSIS: /D must be LAST and must not be quoted.
    $installArgs = @('/S', '/InstallationType=JustMe', '/AddToPath=0', '/RegisterPython=0', "/D=$installDir")
    $p = Start-Process -FilePath $exe -ArgumentList $installArgs -Wait -PassThru
    if ($p.ExitCode -ne 0) { throw "Miniforge installer failed with exit code $($p.ExitCode)" }

    $script:CondaExe = Join-Path $installDir 'Scripts\conda.exe'
    if (-not (Test-Path $script:CondaExe)) { throw "Miniforge installed but conda.exe not found at $script:CondaExe" }
    Remove-Item $exe -ErrorAction SilentlyContinue
    Write-Ok "Miniforge installed: $script:CondaExe"
}

$condaRoot = Split-Path (Split-Path $script:CondaExe -Parent) -Parent
Write-Info "conda root  : $condaRoot"
Write-Info ("conda ver   : " + (& $script:CondaExe --version))

# ---------------------------------------------------------------- 3. create environment
Write-Step "Creating environment '$EnvName'"

$envList   = & $script:CondaExe env list
$envExists = $envList | Select-String -Pattern ("^\s*" + [regex]::Escape($EnvName) + "\s") -Quiet

if ($envExists -and $Force) {
    Write-Warn "environment exists -- removing it because -Force was given"
    Invoke-Conda env remove -y -n $EnvName
    $envExists = $false
}

if ($envExists) {
    Write-Ok "environment '$EnvName' already exists -- reusing it (pass -Force to recreate)"
}
else {
    Write-Info 'solving core packages from conda-forge (this is the slow part)'
    Invoke-Conda create -y -n $EnvName -c conda-forge --override-channels `
        "python=$PythonVer" `
        kwant `
        "numpy<2.5" scipy matplotlib `
        ipykernel jupyterlab
    # numpy<2.5: numpy 2.5.0 (June 2026) removed np.cross on 2-vectors, which the
    # released kwant 1.5.0 still uses in kwant.physics.magnetic_gauge.  The fix is on
    # Kwant's main branch but unreleased; drop the pin once a newer Kwant ships.
    Write-Ok "core environment created"
}

# Persist the numpy pin so that NO later conda install in this environment (the
# extras below, or the user's own) can lift numpy past 2.5 silently.
$envPrefix = (& $script:CondaExe run -n $EnvName python -c "import sys; print(sys.prefix)").Trim()
$pinFile = Join-Path $envPrefix 'conda-meta\pinned'
if (-not (Test-Path (Split-Path $pinFile))) { New-Item -ItemType Directory -Force (Split-Path $pinFile) | Out-Null }
if (-not (Test-Path $pinFile) -or -not (Select-String -Path $pinFile -Pattern '^numpy' -Quiet)) {
    Add-Content -Path $pinFile -Value 'numpy <2.5' -Encoding ascii
}
Write-Ok "numpy<2.5 pinned in $pinFile"

# ---------------------------------------------------------------- 4. optional extras
Write-Step 'Installing optional components (best effort)'

# python-mumps  -> the fast sparse solver; the single biggest performance factor
# sympy         -> required by kwant.continuum  (notebook section 13)
# qsymm         -> required by kwant.qsymm
# plotly        -> interactive / true-3D plotting backend added in Kwant 1.5
# ipympl        -> interactive matplotlib inside notebooks
$extras = [ordered]@{
    'python-mumps' = 'fast sparse solver (kwant.solvers.mumps)'
    'sympy'        = 'symbolic discretisation (kwant.continuum)'
    'qsymm'        = 'symmetry finding (kwant.qsymm)'
    'plotly'       = 'interactive plotting backend'
    'ipympl'       = 'interactive matplotlib in notebooks'
}

foreach ($pkg in $extras.Keys) {
    Write-Info "installing $pkg  --  $($extras[$pkg])"
    if (Invoke-CondaSafe install -y -n $EnvName -c conda-forge --override-channels $pkg "numpy<2.5") {
        Write-Ok "$pkg"
    }
    else {
        Write-Warn "$pkg could not be installed -- continuing without it"
    }
}

# ---------------------------------------------------------------- 5. Jupyter kernel
Write-Step 'Registering the Jupyter kernel'

Invoke-Conda run -n $EnvName python -m ipykernel install --user `
    --name $EnvName --display-name "Python ($EnvName)"
Write-Ok "kernel 'Python ($EnvName)' registered -- VS Code and JupyterLab will list it"

# ---------------------------------------------------------------- 6. shell integration
if (-not $SkipInit) {
    Write-Step 'Enabling conda in PowerShell and cmd.exe'

    Invoke-Conda init powershell cmd.exe
    Write-Ok 'conda init done'

    $policy = Get-ExecutionPolicy -Scope CurrentUser
    if ($policy -in @('Restricted', 'Undefined', 'AllSigned')) {
        Write-Warn "PowerShell ExecutionPolicy for CurrentUser is '$policy'."
        Write-Warn 'The conda profile will not load, so `conda activate` will not work in PowerShell.'
        Write-Warn 'Fix with:   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned'
    }
    else {
        Write-Ok "ExecutionPolicy (CurrentUser) = $policy -- conda profile will load"
    }
}
else {
    Write-Step 'Skipping conda init (-SkipInit)'
}

# ---------------------------------------------------------------- 7. verify
Write-Step 'Verifying the installation'

$verify = Join-Path $PSScriptRoot 'verify_kwant.py'
if (Test-Path $verify) {
    & $script:CondaExe run -n $EnvName --no-capture-output python $verify
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "verification script reported a problem (exit $LASTEXITCODE)"
    }
}
else {
    Write-Warn "verify_kwant.py not found next to this script -- running a minimal check instead"
    & $script:CondaExe run -n $EnvName --no-capture-output python -c "import kwant; print('kwant', kwant.__version__)"
}

# The pin must have survived the extras phase: assert the resolved numpy.
$npVer = (& $script:CondaExe run -n $EnvName python -c "import numpy; print(numpy.__version__)").Trim()
if ($npVer -match '^(\d+)\.(\d+)' -and ([int]$Matches[1] -gt 2 -or ([int]$Matches[1] -eq 2 -and [int]$Matches[2] -ge 5))) {
    Write-Warn "numpy $npVer is >= 2.5: kwant.physics.magnetic_gauge will not work (the pin did not hold)"
}
else {
    Write-Ok "numpy $npVer (pin numpy<2.5 held)"
}

# ---------------------------------------------------------------- done

Write-Host ''
Write-Host '===============================================================' -ForegroundColor White
Write-Host '  Done' -ForegroundColor White
Write-Host '===============================================================' -ForegroundColor White
Write-Host ''
Write-Host 'Interpreter path (paste this into VS Code if it does not autodetect):' -ForegroundColor White
Write-Host "    $envPrefix\python.exe" -ForegroundColor Yellow
Write-Host ''
Write-Host 'PowerShell / cmd  -- open a NEW window first, then:' -ForegroundColor White
Write-Host "    conda activate $EnvName" -ForegroundColor Yellow
Write-Host '    python -c "import kwant; print(kwant.__version__)"' -ForegroundColor Yellow
Write-Host ''
Write-Host 'VS Code:' -ForegroundColor White
Write-Host '    1. Install the "Python" and "Jupyter" extensions (Microsoft).' -ForegroundColor Gray
Write-Host '    2. Open Kwant_Theory_and_Practice.ipynb' -ForegroundColor Gray
Write-Host '    3. Click "Select Kernel" (top right) -> Python Environments ->' -ForegroundColor Gray
Write-Host "       Python ($EnvName)" -ForegroundColor Gray
Write-Host '    4. Run All.' -ForegroundColor Gray
Write-Host ''
Write-Host 'JupyterLab:' -ForegroundColor White
Write-Host "    conda activate $EnvName" -ForegroundColor Yellow
Write-Host '    jupyter lab' -ForegroundColor Yellow
Write-Host ''
