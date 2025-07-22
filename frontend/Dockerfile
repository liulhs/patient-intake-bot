# 使用 Node.js 22 作为基础镜像
FROM node:22-alpine AS builder

# 设置工作目录
WORKDIR /app

# 复制 package.json 和 yarn.lock
COPY package*.json yarn.lock ./

# 安装依赖
RUN yarn install

# 复制所有源代码
COPY . .

# 构建应用
RUN yarn build

# 生产环境阶段
FROM node:22-alpine AS runner

WORKDIR /app

# 设置为生产环境
ENV NODE_ENV production

# 复制必要文件
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# 暴露端口
EXPOSE 3000

# 启动应用
CMD ["yarn", "start"]
