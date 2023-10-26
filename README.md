# WebVirtBackend #

WebVirtBackend is an open-source Django-based backend for managing virtual machines in a KVM (Kernel-based Virtual Machine) environment. It is designed to be used with WebVirtCloud, a web interface for managing virtual machines. This project is packaged as a Docker Compose environment for easy deployment.

## Getting Started ##

### Prerequisites ###

* Docker
* Docker Compose

### Installation ###

1. Clone the repository
```bash
git clone https://github.com/webvirtcloud/webvirtbackend.git
```

2. Change into the cloned directory:
```bash
cd webvirtbackend
```

3. Build the Docker image:
```bash
docker compose build
```

4. Run the Docker container:
```bash
docker compose up -d
```

5. Run the database migrations:
```bash
docker compose exec backend python3 manage.py migrate
```

6. Load the initial data:
```bash
docker compose exec backend python3 manage.py loaddata initial_data
```

7. Access the admin site:

Open your web browser and go to `http://localhost:8000/admin`. You can log in with the following credentials:

* Username: `admin@webvirt.cloud`
* Password: `admin`

## Configuration ##

You can configure the backend by editing the `webvirtcloud/settings/local.py` file for modifying the default settings. The default settings are defined in `webvirtcloud/settings/base.py`.

### Swagger ###

The Swagger API documentation is available at `http://localhost:8000/swagger/`.

## Usage ##

The API endpoints are available at `http://localhost:8000/api/`. You can use them to create, delete, and manage virtual machines. You can log in with the following credentials:

* Username: `user@webvirt.cloud`
* Password: `1qaz2wsx`
* Token: `fcc69bfad35527d087bf22a8a84a4f6c3b75387877c78ae3050e9e8036ef`

Example API requests:

```bash
curl -H "Authorization: Bearer fcc69bfad35527d087bf22a8a84a4f6c3b75387877c78ae3050e9e8036ef" http://localhost:8000/api/v1/virtances/
```

## Contributing ##

If you want to contribute to WebVirtBackend, please read the contributing guidelines first (Coming soon).

## License ##

WebVirtBackend is released under the Apache 2.0 Licence.
