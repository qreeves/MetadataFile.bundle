## About

This is a Plex Media Server agent for retrieving metadata from files you place alongside your media. It can be helpful for auto-categorizing files.

## License

Plex Agent 'MetadataFile' is covered under the ZLIB license, you may use the source code so long as you obey this license.

* Copyright (C) 2018 Quinton Reeves

This software is provided 'as-is', without any express or implied warranty. In no event will the authors be held liable for any damages arising from the use of this software. Permission is granted to anyone to use this software for any purpose, including commercial applications, and to alter it and redistribute it freely, subject to the following restrictions:

* The origin of this software must not be misrepresented; you must not claim that you wrote the original software. If you use this software in a product, an acknowledgment in the product documentation would be appreciated but is not required.
* Altered source versions must be plainly marked as such, and must not be misrepresented as being the original software.
* This notice may not be removed or altered from any source distribution.

## Usage

There are two types of files, *metadata* and *catalog*. The agent will recurse back through the directory tree looking for these files.

### Metadata Files

Metadata files can either be the name of the first part with ".ini" appended (specific), or "_metadata" (general). They contain a `[metadata]` header, an options named for each metadata section (see below).

### Catalog Files

Catalog files are just named "_catalog" and contain headers that are a regular expression match against the "media title", and contain the same options as metadata files (see below)

## Metadata Options

```
content_rating_age=<integer>
content_rating=<age rating>
year=<integer>
title=<string>
studio=<string>
tagline=<string>
summary=<string>
trivia=<string>
quotes=<string>
genres=<comma separated list>
writers=<comma separated list>
directors=<comma separated list>
producers=<comma separated list>
countries=<comma separated list>
collections=<comma separated list>
```
