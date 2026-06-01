$ErrorActionPreference = 'Stop'

$packageArgs = @{
  packageName   = 'orbitswipe'
  fileType      = 'exe'
  url           = 'https://orbitswipe.vercel.app/OrbitSwipe.exe'
  silentArgs    = '/S'
  validExitCodes= @(0)
  softwareName  = 'OrbitSwipe'
  checksum      = '71a7b5d16d50a62541fa2c06fc2181c1d6ce61f1396847f44799733194e573d8'
  checksumType  = 'sha256'
}

Install-ChocolateyPackage @packageArgs
