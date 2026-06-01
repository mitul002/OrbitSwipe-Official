$ErrorActionPreference = 'Stop'

$packageArgs = @{
  packageName   = 'orbitswipe'
  fileType      = 'exe'
  url           = 'https://orbitswipe.vercel.app/OrbitSwipe.exe'
  silentArgs    = '/S'
  validExitCodes= @(0)
  softwareName  = 'OrbitSwipe'
  checksum      = '4353D752B930CBC984B7735DA982A000D929BB12A51F5B643EF5219A412F15E0'
  checksumType  = 'sha256'
}

Install-ChocolateyPackage @packageArgs
