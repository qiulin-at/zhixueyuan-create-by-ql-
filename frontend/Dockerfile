# 前端产物由宿主 `npm run build` 生成；容器内 npm 在代理环境下不稳定
FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY dist /usr/share/nginx/html

EXPOSE 80