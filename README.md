# dan &mdash; DNS-Based Agent Naming

```dan``` is a proof-of-concept (PoC) reference implementation of the IETF Internet-Draft **DNS-Based Agent Naming (DAN): AIDISCA and AIINDEX Resource Records for AI Agent Discovery**.

**DAN Internet-Draft: https://datatracker.ietf.org/doc/draft-seethiraju-dawn-dan/**

The DAN draft defines a DNS-based approach for publishing and discovering AI agents using two new DNS Resource Record (RR) types:
- **AIDISCA** (AI Discovery Record): Publishes the `necessary and sufficient` metadata to securely locate and communicate with an AI agent.
- **AIINDEX** (AI Index Record): Advertizes AI agent publication names available within a DNS zone.

Together, these records enable AI agents to be named, discovered, and trusted using existing DNS infrastructure, including DNSSEC and DANE.

The repository provides tools to:
- Generate AIDISCA records (`TYPE65501`)
- Generate AIINDEX records (`TYPE65502`)

DAN records are generated using RFC3597 presentation format, allowing them to be deployed today using existing DNS software and DNS hosting platforms without requiring native support for the DAN record types. 

---

## Installation

```bash
# Clone the repo
git clone git@github.vrsn.com:product-architecture/dan.git
cd dan

# Create a Python virtual env
python3 -m venv {PATH_TO_ENV}
source {PATH_TO_ENV}/bin/activate

# Install required Python packages
python3 -m pip install -r requirements.txt

```

---

# Tools

The DAN reference implementation currently provides two command-line tools:

## dan-gen

Generates AIDISCA and AIINDEX resource records from agent metadata and outputs them in RFC3597 presentation format suitable for publication in DNS zones.

Supported operations:

- Generate AIDISCA records (`aidisca`)
- Generate AIINDEX records (`aiindex`)

## dan-discover

Discovers published DAN records from DNS and presents them in a human-readable format.

Supported operations:

- Discover AIINDEX record (`aiindex`) for a specified DNS zone
- Discover AIDISCA records (`aidisca`) for a known agent name

> Note: This repository is a proof-of-concept implementation and is intended to demonstrate record generation and discovery workflows described in DAN Internet-Draft.

---

# Publishing an Agent

Suppose you operate an MCP agent at:
    ```
    https://mcp.namestudioapi.com
    ```

- **Generate an AIDISCA record**
    ```bash
    python3 dan-gen.py aidisca \
      --proto mcp \
      --domain domainfinder._agents.namestudioapi.com \
      --endpoint https://mcp.namestudioapi.com \
      --cert-file nsapi-mcp-cert.pem
    ```
    Output:
    ```dns
    domainfinder._agents.namestudioapi.com. 60 IN TYPE65501 \# 124 010301010033001D00200000636865636B5F646F6D61696E5F6E616D655F617661696C6162696C6974792C737567676573745F646F6D61696E5F6E616D657368747470733A2F2F6D63702E6E616D6573747564696F6170692E636F6DED9B9E3AA409069B1833397D9CA65FC46DC1E689961497048BF3D55EEE5152CD
    ```

- Optionally, advertise published AI agents for the zone using **AIINDEX record**
    ```bash
    python3 dan-gen.py aiindex \
      --domain _agents.namestudioapi.com \
      --agents domainfinder._agents.namestudioapi.com
    ```
    Output:
    ```dns
    _agents.namestudioapi.com. 60 IN TYPE65502 \# 77 004900000B73756767657374696F6E73075F6167656E74730A6E616D6573747564696F03636F6D000C617661696C6162696C697479075F6167656E74730A6E616D6573747564696F03636F6D00
    ```
- The generated records can be copied directly into a DNS zone file and published using existing DNS software through RFC3597 generic record support.

## Certificate Handling

The `--cert-file` parameter specifies the certificate material to be encoded into the generated AIDISCA record.

> Note: `dan-gen` does not validate that the supplied certificate corresponds to the specified endpoint or domain. The certificate is encoded directly into the generated record. Publishers are responsible for ensuring that the certificate and endpoint are correctly associated. Mismatches may result in verification failures during subsequent protocol interactions.

---

# Discovering an Agent

Suppose you want to discover a previously published MCP agent:
    ```
    domainfinder._agents.namestudioapi.com
    ```

- **Discover AIINDEX record for a zone**

    ```bash
    python3 dan-discover.py aiindex \
      --domain _agents.namestudioapi.com
    ```
    Output:
    ```text
    Found 1 AIINDEX record(s)

    Domain Name : _agents.namestudioapi.com

    AIINDEX Record
    --------------

    AI Agent Domain Name List:
    - domainfinder._agents.namestudioapi.com.
    ```

- **Discover an AIDISCA record**

    ```bash
    python3 dan-discover.py aidisca \
      --domain domainfinder._agents.namestudioapi.com
    ```
    Output:
    ```text
    Found 1 AIDISCA record(s)

    Agent Name : domainfinder._agents.namestudioapi.com

    AI Agent Proto               : MCP (1)
    Capabilities                 : check_domain_name_availability,suggest_domain_names
    Service Endpoint             : https://mcp.namestudioapi.com
    Cert Usage                   : 3
    Selector                     : 1
    Matching Type                : 1
    Certificate Association Data : ED9B9E3AA409069B1833397D9CA65FC46DC1E689961497048BF3D55EEE5152CD
    Extensions                   : none
    ```
The discovery tool performs DNS lookups for published DAN resource records and presents the extracted metadata in human-readable format.

---

# AI Agent Metadata Extraction

The DAN approach requires only protocol, capabilities, endpoint, and certificate metadata.

To simplify publication, ```dan-gen``` derives capabilities from the agent's MCP endpoint or A2A agent card, allowing an AI agent to be published using only:
* **Protocol** (MCP or A2A)
* **Domain** (AI agent publication name)
* **Endpoint** (for MCP) or **Agent Card** (for A2A)
* **Certificate**
  
The resulting AI agent's necessary and sufficient metadata is encoded by ```dan-gen``` into AIDSICA and AIINDEX records. Advanced users may optionally override derived values such and capabilities and DANE parameters.

---

## Detailed Examples

1. Generate an AIDISCA Record (MCP)

    - Basic Usage command:
        ```bash
        python3 dan-gen.py aidisca \
          --proto mcp \
          --domain domainfinder._agents.namestudioapi.com \
          --endpoint https://mcp.namestudioapi.com \
          --cert-file nsapi-mcp-cert.pem
        ```        
        Output:        
        ```dns
        domainfinder._agents.namestudioapi.com. 60 IN TYPE65501 \# 124 010301010033001D00200000636865636B5F646F6D61696E5F6E616D655F617661696C6162696C6974792C737567676573745F646F6D61696E5F6E616D657368747470733A2F2F6D63702E6E616D6573747564696F6170692E636F6DED9B9E3AA409069B1833397D9CA65FC46DC1E689961497048BF3D55EEE5152CD
        ```

    - Presentation Format (`--pf`) command:
        ```bash
        python3 dan-gen.py aidisca \
          --proto mcp \
          --domain domainfinder._agents.namestudioapi.com \
          --endpoint https://mcp.namestudioapi.com \
          --cert-file nsapi-mcp-cert.pem \
          --pf
        ```
        Output:
        ```dns
        domainfinder._agents.namestudioapi.com. 60 IN TYPE65501 \# 124 010301010033001D00200000636865636B5F646F6D61696E5F6E616D655F617661696C6162696C6974792C737567676573745F646F6D61696E5F6E616D657368747470733A2F2F6D63702E6E616D6573747564696F6170692E636F6DED9B9E3AA409069B1833397D9CA65FC46DC1E689961497048BF3D55EEE5152CD

        Presentation Format
        ----------------------
        domainfinder._agents.namestudioapi.com. 60 IN AIDISCA (
          1 3 1 1
          "check_domain_name_availability,suggest_domain_names"
          "https://mcp.namestudioapi.com"
          ED9B9E3AA409069B1833397D9CA65FC46DC1E689961497048BF3D55EEE5152CD
        )
        ```

    - Verbose Output (`--verbose`) command:
        ```bash
        python3 dan-gen.py aidisca \
          --proto mcp \
          --domain domainfinder._agents.namestudioapi.com \
          --endpoint https://mcp.namestudioapi.com \
          --cert-file nsapi-mcp-cert.pem \
          --verbose
        ```        
        Output:        
        ```dns
        domainfinder._agents.namestudioapi.com. 60 IN TYPE65501 \# 124 010301010033001D00200000636865636B5F646F6D61696E5F6E616D655F617661696C6162696C6974792C737567676573745F646F6D61696E657368747470733A2F2F6D63702E6E616D6573747564696F6170692E636F6DED9B9E3AA409069B1833397D9CA65FC46DC1E689961497048BF3D55EEE5152CD
        
        Presentation Format
        ----------------------        
        domainfinder._agents.namestudioapi.com. 60 IN AIDISCA (
          1 3 1 1
          "check_domain_name_availability,suggest_domain_names"
          "https://mcp.namestudioapi.com"
          ED9B9E3AA409069B1833397D9CA65FC46DC1E689961497048BF3D55EEE5152CD
        )
        
        AIDISCA Record Summary
        ----------------------        
        Domain Name                  : domainfinder._agents.namestudioapi.com.
        AI Agent Proto               : MCP (1)
        Capabilities                 : check_domain_name_availability,suggest_domain_names
        Capabilities Source          : Successfully extracted from MCP tools/list via official MCP Python SDK
        Service Endpoint             : https://mcp.namestudioapi.com
        Cert Usage                   : 3
        Selector                     : 1
        Matching Type                : 1
        Certificate Source           : nsapi-mcp-cert.pem
        Certificate Association Data : ED9B9E3AA409069B1833397D9CA65FC46DC1E689961497048BF3D55EEE5152CD
        Extensions                   : none
        ```

2. Generate an AIDISCA Record (A2A)

    - Verbose Output (`--verbose`) command:
        ```bash
        python3 dan-gen.py aidisca \
          --proto a2a \
          --domain aiblog._agents.colinmcnamara.com \
          --card https://colinmcnamara.com/.well-known/agent.json \
          --cert-file colin-a2a-cert.pem \
          --verbose
        ```        
        Output:        
        ```dns
        aiblog._agents.colinmcnamara.com. 60 IN TYPE65501 \# 198 02030101003D0029002000346C6973745F706F7374732C6765745F706F73742C7365617263685F706F7374732C6765745F6D657461646174612C6765745F617574686F725F696E666F68747470733A2F2F636F6C696E6D636E616D6172612E636F6D2F6170692F6132612F7365727669636561DBBB157AB4F63987D4250C05A11E0854E38CA56826A47CFEE486075FB1ADE80001003068747470733A2F2F636F6C696E6D636E616D6172612E636F6D2F2E77656C6C2D6B6E6F776E2F6167656E742E6A736F6E
        
        Presentation Format
        ----------------------                
        aiblog._agents.colinmcnamara.com. 60 IN AIDISCA (
          2 3 1 1
          "list_posts,get_post,search_posts,get_metadata,get_author_info"
          "https://colinmcnamara.com/api/a2a/service"
          61DBBB157AB4F63987D4250C05A11E0854E38CA56826A47CFEE486075FB1ADE8
          "\000\001\000\060https://colinmcnamara.com/.well-known/agent.json"
        )
        
        AIDISCA Record Summary
        ----------------------        
        Domain Name                  : aiblog._agents.colinmcnamara.com.
        AI Agent Proto               : A2A (2)
        Capabilities                 : list_posts,get_post,search_posts,get_metadata,get_author_info
        Capabilities Source          : A2A Agent Card
        Service Endpoint             : https://colinmcnamara.com/api/a2a/service
        Cert Usage                   : 3
        Selector                     : 1
        Matching Type                : 1
        Certificate Source           : colin-a2a-cert.pem
        Certificate Association Data : 61DBBB157AB4F63987D4250C05A11E0854E38CA56826A47CFEE486075FB1ADE8
        Extensions                   : Agent Card = https://colinmcnamara.com/.well-known/agent.json
        ```

3. Generate an AIINDEX Record

    - Basic Usage command:
        ```bash
        python3 dan-gen.py aiindex \
          --domain _agents.namestudioapi.com \
          --agents domainfinder._agents.namestudioapi.com
        ```        
        Output:        
        ```dns
        _agents.namestudioapi.com. 60 IN TYPE65502 \# 77 004900000B73756767657374696F6E73075F6167656E74730A6E616D6573747564696F03636F6D000C617661696C6162696C697479075F6167656E74730A6E616D6573747564696F03636F6D00
        ```

    - Presentation Format (`--pf`) command:
        ```bash
        python3 dan-gen.py aiindex \
          --domain _agents.namestudioapi.com \
          --agents domainfinder._agents.namestudioapi.com
          --pf
        ```        
        Output:        
        ```dns
        _agents.namestudioapi.com. 60 IN TYPE65502 \# 77 004900000B73756767657374696F6E73075F6167656E74730A6E616D6573747564696F03636F6D000C617661696C6162696C697479075F6167656E74730A6E616D6573747564696F03636F6D00
        
        Presentation Format
        ----------------------        
        _agents.namestudioapi.com. 60 IN AIINDEX (
          domainfinder._agents.namestudioapi.com
        )
        ```

    - Verbose Output (`--verbose`) command:
        ```bash
        python3 dan-gen.py aiindex \
          --domain _agents.namestudioapi.com \
          --agents domainfinder._agents.namestudioapi.com
          --verbose
        ```        
        Output:        
        ```dns
        _agents.namestudioapi.com. 60 IN TYPE65502 \# 77 004900000B73756767657374696F6E73075F6167656E74730A6E616D6573747564696F03636F6D000C617661696C6162696C697479075F6167656E74730A6E616D6573747564696F03636F6D00
        
        Presentation Format
        ----------------------        
        _agents.namestudioapi.com. 60 IN AIINDEX (
          domainfinder._agents.namestudioapi.com
        )

        AIINDEX Record Summary
        ----------------------                
        Domain Name                  : _agents.namestudioapi.com.
        AI Agent Domain Name List    :
          - domainfinder._agents.namestudioapi.com.
        Extensions                   : none
        ```
