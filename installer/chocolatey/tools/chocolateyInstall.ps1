$ErrorActionPreference = 'Stop'

$packageArgs = @{
  packageName   = 'orbitswipe'
  fileType      = 'exe'
  url           = 'https://orbitswipe.vercel.app/OrbitSwipe.exe'
  silentArgs    = '/S'
  validExitCodes= @(0)
  softwareName  = 'OrbitSwipe'
  checksum      = 'F7F61389E07532CDDD81AE8479548BEF65B6F03FA41A296AA0C5E60E4F0E2866'
  checksumType  = 'sha256'
}

Install-ChocolateyPackage @packageArgs
