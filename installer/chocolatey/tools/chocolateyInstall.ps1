$ErrorActionPreference = 'Stop'

$packageArgs = @{
  packageName   = 'orbitswipe'
  fileType      = 'exe'
  url           = 'https://orbitswipe.vercel.app/OrbitSwipe.exe'
  silentArgs    = '/S'
  validExitCodes= @(0)
  softwareName  = 'OrbitSwipe'
  checksum      = 'C5925460C65DEC9D1F852F687EF2C46B7E5457C040C8EDC5AA0B4239EA03AA82'
  checksumType  = 'sha256'
}

Install-ChocolateyPackage @packageArgs
