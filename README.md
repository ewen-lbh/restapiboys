# RESTAPIBOYS: REST APIs Based On YAML Specifications

--------------------------------------------------------

__This project is in an early stage, and does not work at all yet.__

_The following list tracks broad topics that need to be implemented before the framework can be considered 'usable'_:

- [x] Endpoints definition handling
- [ ] Routing (WIP)
- [ ] Database interactions
- [ ] Authentification
- [ ] Serialization
- [ ] Request validation (WIP)
- [ ] Database table creation & migration

--------------------------------------------------------

<center>
Create REST APIs for modern web applications, while keeping your code DRY. Finally.
</center>

We all keep reinventing the wheel. Every web application has a bunch of resources, each owned by users, those users can log in, reset their passwords, and can only access their own resources. They need to obtain access tokens, those can be refreshed with refresh tokens.

Those resources are stored in a database, have a model describing their fields.
Those same fields are described in serializers, which describe how the API will send & receive data.

A resource has 5 endpoints. Imagine this API has a certain resource named `notes`

- `GET /notes/` - Returns the list of resources owned by the user
- `GET /notes/:uuid` - Returns information about a single resource whose unique identifier is `:uuid`.
- `POST /notes/` - Add a new `note` owned by the current user
- `PATCH /notes/:uuid` - Modify a `note`
- `DELETE /notes/:uuid` - Delete a `note`

If your API is within those bounds, you can use RESTAPIBOYS.

But wait! How about edge cases? What if some endpoint is not tied to a database model?

And that's where most framework creators would've though 'huh, need to take care of _all_ of these edge cases, no I need to keep things less DRY'.

But how about this:

- Most resources are indeed perfectly tied to database models
- _some_ endpoints are not, and need special logic

For those special endpoints, we fall back to plain python code. But how about the majority of endpoints? Do you want to waste your time defining **5** endpoints are copy-pasting code?

I don't.

That's why I created this framework.

Let's see how you would define the `note` resource I talked about earlier

<center> <em> src/resources/notes.yaml </em> </center>

```yaml
title:
  is: string
  max length: 500
  default: ""
  allow empty: yes

content:
  is: string
  default: ""
  allow empty: yes
  # The content of the note is too big to be included in the "list" endpoint.
  # Only include it in /notes/:uuid endpoints
  omit in:
    - list
  validation:
    External notes must point to a valid URL: type != 'html' or is_url(content)

thumbnail():
  is: string
  computation:
    react: 
      - content
      - title
    set: endpoint(f'notes/{uuid}/thumbnail')

type:
  one of:
    - html
    - markdown
    - asciidoc
    - external # The content becomes the URL pointing to the note
  default: html
```

Thats all?

Well, yes.

This is enough to:

- create a model
- define the **5** API endpoints
- define the documentation entry

Documentation coming soon.
You can take a look at the example to see how an API (schoolsyst's) would be implemented.
