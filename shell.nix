{ pkgs ? import <nixpkgs> {} }:

pkgs.python310Packages.buildPythonPackage rec {
  name = "mypackage";
  src = ./.;
  propagatedBuildInputs = with pkgs.python310Packages; [
    pkgs.python310
    pyyaml
    xdg-base-dirs
    rich
    google-cloud-texttospeech
  ];
}

#pkgs.mkShellNoCC {
#  packages = with pkgs; [
#    (python3.withPackages (ps: with ps; [
#      pyyaml
#      xdg-base-dirs
#      rich
#      google-cloud-texttospeech
#    ]))
#  ];
#}
