$ErrorActionPreference = 'Stop'

$packageArgs = @{
  packageName   = 'orbitswipe'
  fileType      = 'exe'
  url           = 'https://orbitswipe.vercel.app/OrbitSwipe.exe'
  silentArgs    = '/S'
  validExitCodes= @(0)
  softwareName  = 'OrbitSwipe'
  checksum      = '74E026DBD3B3A09017EDC9AAA8F369E1F7C86F5995D58689587EB5385BCAC7D5'
  checksumType  = 'sha256'
}

Install-ChocolateyPackage @packageArgs
