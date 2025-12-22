{ config, pkgs, ... }:

{
  # ---------------------------------------------------------------------
  # 1. Firewall Configuration
  # ---------------------------------------------------------------------
  # Open ports 80 (HTTP) and 443 (HTTPS) to allow web traffic and 
  # Let's Encrypt validation.
  networking.firewall.allowedTCPPorts = [ 80 443 ];

  # ---------------------------------------------------------------------
  # 2. SSL / Let's Encrypt Configuration
  # ---------------------------------------------------------------------
  # Needed for automatic HTTPS certificates.
  security.acme.acceptTerms = true;
  # TODO: Replace with your actual email address for certificate notifications
  security.acme.defaults.email = "info@printbrigata.ch"; 

  # ---------------------------------------------------------------------
  # 3. Nginx Reverse Proxy
  # ---------------------------------------------------------------------
  services.nginx = {
    enable = true;
    recommendedProxySettings = true;
    recommendedTlsSettings = true;

    virtualHosts."rechnung.printbrigata.ch" = {
      enableACME = true;
      forceSSL = true;
      locations."/" = {
        proxyPass = "http://127.0.0.1:8501";
        proxyWebsockets = true; # Valid for Streamlit WebSocket connections
      };
    };
  };

  # ---------------------------------------------------------------------
  # 4. Systemd Service for Streamlit
  # ---------------------------------------------------------------------
  systemd.services.printbrigata-tool = {
    description = "Printbrigata Rechnungstool";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    
    serviceConfig = {
      # Run as your user so it can access the files in your home directory
      User = "meo";
      WorkingDirectory = "/home/meo/Dokumente/Printbrigata/Rechnungstool/rechnungs-tool";
      
      # Restart automatically if it crashes
      Restart = "always";
      RestartSec = "5s";

      # Use nix-shell to set up the environment (libs) and then source the venv
      ExecStart = ''
        ${pkgs.nix}/bin/nix-shell /home/meo/Dokumente/Printbrigata/Rechnungstool/rechnungs-tool/shell.nix --run "source .venv/bin/activate && python -m streamlit run Preislisten.py --server.port 8501 --server.address 127.0.0.1 --server.headless true"
      '';
    };
  };
}
