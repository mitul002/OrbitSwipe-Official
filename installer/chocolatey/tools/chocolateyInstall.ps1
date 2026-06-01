$ErrorActionPreference = 'Stop'

$packageArgs = @{
  packageName   = 'orbitswipe'
  fileType      = 'exe'
  url           = 'https://orbitswipe.vercel.app/OrbitSwipe.exe'
  silentArgs    = '/S'
  validExitCodes= @(0)
  softwareName  = 'OrbitSwipe'
  checksum      = '9CF04058D9147E7AC0F3D8D6E9085D124AD57119677817378795417895250787'
  checksumType  = 'sha256'
}

Install-ChocolateyPackage @packageArgs
