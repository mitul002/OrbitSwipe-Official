$ErrorActionPreference = 'Stop'

$packageArgs = @{
  packageName   = 'orbitswipe'
  fileType      = 'exe'
  url           = 'https://orbitswipe.vercel.app/OrbitSwipe.exe'
  silentArgs    = '/S'
  validExitCodes= @(0)
  softwareName  = 'OrbitSwipe'
  checksum      = '026DB0238A9AC1D67F534B8800AE916C95FDB1FD1364F90BF4ED80F156B7825A'
  checksumType  = 'sha256'
}

Install-ChocolateyPackage @packageArgs
