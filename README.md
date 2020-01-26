# Simple WSGI server
This is WSGI based server based on these pages.
- [Let’s Build A Web Server\. Part 1\. \- Ruslan's Blog](https://ruslanspivak.com/lsbaws-part1/)
- [Let’s Build A Web Server\. Part 2\. \- Ruslan's Blog](https://ruslanspivak.com/lsbaws-part2/)
- [Let’s Build A Web Server\. Part 3\. \- Ruslan's Blog](https://ruslanspivak.com/lsbaws-part3/)

# How to run
[poetry](https://github.com/python-poetry/poetry) is used in this repository.
```
$ git clone git@github.com:python-poetry/poetry.git

$ poetry install

// launch simple web app
$ poetry run python wsgi_server.py wsgi_app:app

// you can access using port 8888
$ curl http://localhost:8888
```