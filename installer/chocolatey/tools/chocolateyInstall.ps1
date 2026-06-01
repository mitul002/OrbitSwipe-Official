$ErrorActionPreference = 'Stop'

$packageArgs = @{
  packageName   = 'orbitswipe'
  fileType      = 'exe'
  url           = 'https://orbitswipe.vercel.app/OrbitSwipe.exe'
  silentArgs    = '/S'
  validExitCodes= @(0)
  softwareName  = 'OrbitSwipe'
  checksum      = '5B64644F0847CF69D55FF15F264D290770489658BB6333F05840BAAD5D1D4F12'
  checksumType  = 'sha256'
}

Install-ChocolateyPackage @packageArgs
