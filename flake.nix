{
  description = "kiri";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix.url = "github:nix-community/poetry2nix";
    poetry2nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = inputs@{ self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };
      in rec
      {
        devShells.default = pkgs.mkShell {
          name = "kiri";
          buildInputs = with pkgs; [
            (pkgs.poetry2nix.mkPoetryEnv {
              projectDir = ./.;
            })
            poetry
          ];
        };

        packages.kiri = pkgs.poetry2nix.mkPoetryApplication {
          projectDir = ./.;
          meta = with pkgs.lib; {
            description = "A friendly discord reminder that school's about to close!";
            homepage = "https://github.com/starcraft66/kiri/";
            license = licenses.mit;
            maintainers = [ maintainers.starcraft66 ];
          };
        };

        dockerImage = pkgs.dockerTools.buildImage {
          name = "attention-attention";
          tag = packages.kiri.version;
          contents = with pkgs; [
            bashInteractive
            busybox
            tzdata
          ];
          config = {
            Env = [
              "SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
            ];
            Cmd = [ "${packages.kiri}/bin/python" "-m" "kiri" ];
          };
        };
      }
    );
}
