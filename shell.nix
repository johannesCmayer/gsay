{ pkgs ? import <nixpkgs> {} }:

pkgs.python310Packages.buildPythonPackage rec {
  name = "mypackage";
  src = ./.;
  propagatedBuildInputs = with pkgs.python310Packages; [
    pkgs.poetry
    pkgs.python310
    pyyaml
    xdg-base-dirs
    rich
    google-cloud-texttospeech
  ];
}

# pkgs.mkShell {
#   packages = with pkgs; [
#     poetry
#     (python3.withPackages (ps: with ps; [
#       pyyaml
#       xdg-base-dirs
#       rich
#       google-cloud-texttospeech
#     ]))
#   ];
# }
