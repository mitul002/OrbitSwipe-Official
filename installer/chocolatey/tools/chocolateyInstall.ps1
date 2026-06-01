$ErrorActionPreference = 'Stop'

$packageArgs = @{
  packageName   = 'orbitswipe'
  fileType      = 'exe'
  url           = 'https://orbitswipe.vercel.app/OrbitSwipe.exe'
  silentArgs    = '/S'
  validExitCodes= @(0)
  softwareName  = 'OrbitSwipe'
  checksum      = 'A2563D8F0E0C49F9B02D8313564D134C483F45A8BADABD4CA0C81CAF10CB027D'
  checksumType  = 'sha256'
}

Install-ChocolateyPackage @packageArgs
