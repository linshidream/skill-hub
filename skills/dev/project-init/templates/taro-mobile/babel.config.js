// babel.config.js —— Taro3.6 babel 预设（babel-preset-taro 与 @tarojs/* 同版本）
module.exports = {
  presets: [
    ["taro", {
      framework: "react",
      ts: true,
      compiler: "webpack5",
    }],
  ],
};
