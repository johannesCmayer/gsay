{ pkgs ? import <nixpkgs> {} }:
pkgs.callPackage ./app.nix {}