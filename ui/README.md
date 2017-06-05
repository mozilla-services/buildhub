# Web UI

The Web UI is written in Elm.

## Setting up the development environment

    $ npm i
    $ ./node_modules/.bin/elm-package install

## Starting the dev server

    $ npm start

## Starting the dev server in live debug mode

    $ npm run debug

### Building

    $ npm run build

### Optimizing

    $ npm run optimize

This command compresses and optimizes the generated js bundle. It usually allows reducing its size by ~75%, at the cost of the JavaScript code being barely readable. Use this command for deploying the buildhub ui to production.

### Deploying to gh-pages

    $ npm run deploy

The app should be deployed to https://[your-github-username].github.io/buildhub/

Note: The `deploy` command uses the `optimize` one internally.

## Launching testsuite

    $ npm test
