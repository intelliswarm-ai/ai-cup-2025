FROM redimp/otterwiki:latest

# Install Python and bash (if not already present)
USER root
RUN apt-get update && apt-get install -y python3 bash && rm -rf /var/lib/apt/lists/*

# Copy wiki generation script
COPY generate_wiki_pages.py /usr/local/bin/
COPY wiki-init.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/wiki-init.sh /usr/local/bin/generate_wiki_pages.py

# Create entrypoint that runs initialization before starting OtterWiki
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
