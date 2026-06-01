$ErrorActionPreference = 'Stop'

$packageArgs = @{
  packageName   = 'orbitswipe'
  fileType      = 'exe'
  url           = 'https://orbitswipe.vercel.app/OrbitSwipe.exe'
  silentArgs    = '/S'
  validExitCodes= @(0)
  softwareName  = 'OrbitSwipe'
  checksum      = 'EEB0E83FC279D6E4580AED5A2F412C2F23E242145B8EB952098019DF34D85AB9'
  checksumType  = 'sha256'
}

Install-ChocolateyPackage @packageArgs
