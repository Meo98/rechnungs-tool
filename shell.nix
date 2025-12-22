{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = [
    pkgs.python312
    pkgs.python312Packages.pip
    pkgs.python312Packages.virtualenv
  ];

  buildInputs = with pkgs; [
    cairo
    pango
    gdk-pixbuf
    glib
  ];

  shellHook = ''
    export LD_LIBRARY_PATH=${pkgs.cairo}/lib:${pkgs.pango}/lib:${pkgs.gdk-pixbuf}/lib:${pkgs.glib.out}/lib:$LD_LIBRARY_PATH
    echo "Environment set up for Printbrigata Invoice Tool"
    echo "System libraries added to LD_LIBRARY_PATH: cairo, pango, gdk-pixbuf, glib"
  '';
}
