FROM node:24-alpine
ENV NODE_ENV=production
RUN mkdir -p /app &&\
chown -R node:node /app
WORKDIR /app
USER node
COPY --chown=node:node package*.json ./
RUN npm install --omit=dev
COPY --chown=node:node src/ ./src/
EXPOSE 3000
CMD ["node", "src/index.js"]
