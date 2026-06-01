$ErrorActionPreference = 'Stop'

$packageArgs = @{
  packageName   = 'orbitswipe'
  fileType      = 'exe'
  url           = 'https://orbitswipe.vercel.app/OrbitSwipe.exe'
  silentArgs    = '/S'
  validExitCodes= @(0)
  softwareName  = 'OrbitSwipe'
  checksum      = '08dd1ba2c1117d975f321a763bf47de6a9cccd87f46b18c1209669c40399e271'
  checksumType  = 'sha256'
}

Install-ChocolateyPackage @packageArgs
