{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.ghidra
    pkgs.radare2
    pkgs.neovim
  ];
  shellHook = ''
    export GHIDRA_PATH=$(dirname $(readlink -f $(which ghidra)))
    export PATH=$PATH:$GHIDRA_PATH/support
  '';
}

