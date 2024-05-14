{
  description = "gsay";
  inputs = {};
  outputs = { self, nixpkgs }: {
    packages.x86_64-linux.default =
      # Notice the reference to nixpkgs here.
      with import nixpkgs { system = "x86_64-linux"; };
      stdenv.mkDerivation {
        name = "hello";
        src = self;
        buildPhase = "echo hello";
        installPhase = "echo hello";
      };
  };
}