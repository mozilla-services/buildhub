# Note! If you make changes it in this file, to rebuild it use:
#   docker-compose build ui
#

FROM node:9

# Create app directory
#WORKDIR /usr/src/app

#ADD frontend/yarn.lock /yarn.lock
#ADD ui/package.json /package.json

#COPY ./ui/package*.json .
# Install app dependencies
# A wildcard is used to ensure both package.json AND package-lock.json are copied
# where available (npm@5+)
#COPY ./upackage.json ./
COPY package*.json ./

RUN npm install

# Bundle app source
#COPY ui .

EXPOSE 3000
EXPOSE 35729

CMD [ "npm", "start" ]
