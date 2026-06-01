$ErrorActionPreference = 'Stop'

$packageArgs = @{
  packageName   = 'orbitswipe'
  fileType      = 'exe'
  url           = 'https://orbitswipe.vercel.app/OrbitSwipe.exe'
  silentArgs    = '/S'
  validExitCodes= @(0)
  softwareName  = 'OrbitSwipe'
  checksum      = '1558EA1336E7680B2BB7E7D67EDE13AE9AF225E6C802EBD3BEB9BD3FD8A1D9FC'
  checksumType  = 'sha256'
}

Install-ChocolateyPackage @packageArgs
