Gophish
=======

Gophish: Open-Source Phishing Toolkit

Gophish is an open-source phishing toolkit designed for businesses and penetration testers. It provides the ability to quickly and easily setup and execute phishing engagements and security awareness training.



# NOTICE

**Due to the original gophish repository and project seeming to have no more active maintainers. I have forked this repo.**

**Forked to add new capabilities.**

Most of the documentation hasn't been updated yet to reflect the fork and changes. As things progress they will be.

# New


## Endpoint
- `/campaigns/__id__/results/__rid__`
    - Set the `Reported` value to `True` for a specific campaign result

### Install

### Building From Source
**If you are building from source, please note that Gophish requires Go v1.10 or above!**

To build Gophish from source, simply run ```git clone https://github.com/gophish/gophish.git``` and ```cd``` into the project source directory. Then, run ```go build```. After this, you should have a binary called ```gophish``` in the current directory.


### Setup
After running Gophish, open an Internet browser to https://localhost:3333 and login with the default username and password listed in the log output.
e.g.
```
time="2020-07-29T01:24:08Z" level=info msg="Please login with the username admin and the password 4304d5255378177d"
```

### License
```
Gophish - Open-Source Phishing Framework

The MIT License (MIT)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software ("Gophish Community Edition") and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```
