$ErrorActionPreference = 'Stop'

$packageArgs = @{
  packageName   = 'orbitswipe'
  fileType      = 'exe'
  url           = 'https://orbitswipe.vercel.app/OrbitSwipe.exe'
  silentArgs    = '/S'
  validExitCodes= @(0)
  softwareName  = 'OrbitSwipe'
  checksum      = 'EA407597F79BBFFF64ECA8F33F88056EE39B3A74DC3B708DCBB93C993DC34256'
  checksumType  = 'sha256'
}

Install-ChocolateyPackage @packageArgs
