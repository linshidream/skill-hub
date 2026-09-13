// rebuild-antd-pack.tsx — antd5 预构建起手包 re-build 脚本（happy-dom 提取 CSS + renderToStaticMarkup 出片段 DOM）
// 暗礁：antd 5.29 的 @ant-design/cssinjs 2.x 用 useInsertionEffect 注入 style，SSR 渲染不跑 effect → cache 空，
//   extractStyle / @ant-design/static-style-extract 在 5.29 均失效。
// 解法：happy-dom 模拟 DOM，createRoot+flushSync 跑真实客户端渲染（effect 同步执行）→ cssinjs 注入 <style> 到 head。
//   展厅渲染一次（提取全量 CSS + 展厅 DOM）；片段 DOM 用 renderToStaticMarkup（纯 DOM，快，不需 effect，class 一致因 hashed:false）。
// 产物：prototype-skeleton/antd.static.css（重资产，不入源码 git，靠 release 分发）/ fragments/*.html（轻量，入源码 git）/ index.html（展厅）
// 配置：cssVar:{key:'root'} + hashed:false —— 变量落 :root（post-process .root{→:root{），class 名稳定，agent :root 覆盖变量值即改主题，不重新 build。

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { Window } from 'happy-dom';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ---- 1. happy-dom 全局环境（必须在 import antd / react-dom/client 前）----
const win = new Window() as unknown as typeof globalThis.window;
const doc = win.document;
(globalThis as any).window = win;
(globalThis as any).document = doc;
for (const k of Object.getOwnPropertyNames(win)) {
  if (!(k in globalThis)) { try { (globalThis as any)[k] = (win as any)[k]; } catch {} }
}
if (!(win as any).matchMedia) (win as any).matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {}, dispatchEvent: () => false });
if (!(globalThis as any).matchMedia) (globalThis as any).matchMedia = (win as any).matchMedia;
if (!(globalThis as any).ResizeObserver) (globalThis as any).ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };

// ---- 2. 动态 import antd / react-dom/client（此时全局已就位）----
const antd = await import('antd');
const { createRoot } = await import('react-dom/client');
const { flushSync } = await import('react-dom');
const {
  ConfigProvider, Layout, Menu, Table, Card, Form, Input, Button,
  Empty, Tag, Steps, Breadcrumb, Statistic, List, Space, Typography,
  Descriptions, Result, Row, Col, Avatar, Modal, Select, Drawer, Pagination,
} = antd;

const { Sider, Header, Content } = Layout;
const { Title, Paragraph } = Typography;

const theme = { cssVar: { key: 'root' }, hashed: false, token: { colorPrimary: '#1668DC', borderRadius: 4, fontSize: 14 } };

// Lucide inline SVG helper —— antd Menu item 的 icon 属性接 ReactNode；
// 产物渲染为 <span class="ant-menu-item-icon"><svg class="lucide" ...>…</svg></span><span class="ant-menu-title-content">…</span>
// 作用：让 fragments/layout.html 参考片段与 re-build 产物自带 icon DOM 结构，agent 拼菜单时照此配 icon
const Ic = (paths: React.ReactNode) => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">{paths}</svg>
);

const components: Record<string, React.ReactElement> = {
  layout: (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={240}>
        <div style={{ height: 32, color: '#fff', margin: 16, fontSize: 18, fontWeight: 700 }}>OPC Demo</div>
        <Menu theme="dark" mode="inline" defaultSelectedKeys={['home']} items={[
          { key: 'home', label: '首页', icon: Ic(<><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M9 22V12h6v10"/></>) },
          { key: 'detail', label: '详情', icon: Ic(<><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7z"/><path d="M14 2v5h5"/><path d="M8 13h8"/><path d="M8 17h8"/></>) },
          { key: 'form', label: '表单', icon: Ic(<><path d="M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.375 2.625a2.12 2.12 0 1 1 3 3L12 15l-4 1 1-4Z"/></>) },
          { key: 'empty', label: '空态', icon: Ic(<><path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></>) },
          { key: 'error', label: '异常', icon: Ic(<><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></>) },
        ]} />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px' }}><Title level={4} style={{ margin: 0 }}>首页</Title></Header>
        <Content style={{ margin: 24 }}><Paragraph type="secondary">核心流程入口</Paragraph></Content>
      </Layout>
    </Layout>
  ),
  metric_cards: (
    <Row gutter={12}>
      <Col span={8}><Card><Statistic title="待处理" value={12} /></Card></Col>
      <Col span={8}><Card><Statistic title="处理中" value={8} /></Card></Col>
      <Col span={8}><Card><Statistic title="已完成" value={31} /></Card></Col>
    </Row>
  ),
  object_list: (
    <Card title="业务对象">
      <List itemLayout="horizontal" dataSource={[
        { title: '客户 A 的新需求确认', desc: '查看详情' },
        { title: '客户 B 的流程待推进', desc: '继续处理' },
      ]} renderItem={(item: any) => (
        <List.Item actions={[<a key="a">查看</a>]}>
          <List.Item.Meta avatar={<Avatar>客</Avatar>} title={item.title} description={item.desc} />
        </List.Item>
      )} />
    </Card>
  ),
  table: (
    <Table size="middle" columns={[
      { title: '客户', dataIndex: 'customer', key: 'customer' },
      { title: '需求', dataIndex: 'need', key: 'need' },
      { title: '状态', dataIndex: 'status', key: 'status', render: () => <Tag color="blue">进行中</Tag> },
      { title: '操作', key: 'action', render: () => <a>查看</a> },
    ]} dataSource={[
      { key: '1', customer: '客户 A', need: '新需求确认' },
      { key: '2', customer: '客户 B', need: '流程待推进' },
    ]} />
  ),
  descriptions: (
    <Descriptions title="客户详情" bordered column={1}>
      <Descriptions.Item label="客户名称">客户 A</Descriptions.Item>
      <Descriptions.Item label="联系人">张三</Descriptions.Item>
      <Descriptions.Item label="状态"><Tag color="green">已确认</Tag></Descriptions.Item>
    </Descriptions>
  ),
  form: (
    <Card title="新建需求">
      <Form layout="vertical">
        <Form.Item label="客户名称" name="customer"><Input placeholder="请输入客户名称" /></Form.Item>
        <Form.Item label="需求描述" name="need"><Input.TextArea rows={3} placeholder="请输入需求描述" /></Form.Item>
        <Form.Item><Space><Button type="primary" htmlType="submit">提交</Button><Button>取消</Button></Space></Form.Item>
      </Form>
    </Card>
  ),
  steps: (<Steps current={1} items={[{ title: '需求确认' }, { title: '方案设计' }, { title: '开发' }, { title: '交付' }]} />),
  breadcrumb: (<Breadcrumb items={[{ title: '首页' }, { title: '客户' }, { title: '客户 A 详情' }]} />),
  empty: (<Empty description="暂无数据" />),
  result: (<Result status="warning" title="操作出现异常" subTitle="请稍后重试或联系管理员" extra={<Button type="primary">重试</Button>} />),
  action_row: (
    <Space style={{ justifyContent: 'space-between', width: '100%' }}>
      <Title level={3} style={{ margin: 0 }}>首页</Title>
      <Button type="primary">新建</Button>
    </Space>
  ),
  // ---- 覆盖矩阵：渲染各组件的全变体，确保 cssinjs 注入所有变体样式（agent 手拼 DOM 会用到这些 class）----
  coverage: (
    <div>
      {/* Button 全变体（含 danger）—— 注入 ant-btn-default/link/text/dashed/dangerous */}
      <Space wrap>
        <Button type="primary">主</Button>
        <Button type="default">默认</Button>
        <Button type="dashed">虚线</Button>
        <Button type="link">链接</Button>
        <Button type="text">文本</Button>
        <Button type="primary" danger>危险主</Button>
        <Button danger>危险默认</Button>
        <Button type="link" danger>危险链接</Button>
        <Button type="text" danger>危险文本</Button>
        <Button type="primary" size="small">小主</Button>
        <Button type="primary" size="large">大主</Button>
      </Space>
      {/* Tag 状态预设 + 全预设色 —— 注入 ant-tag-success/warning/error/default + 各色 */}
      <Space wrap style={{ display: 'flex', marginTop: 8 }}>
        <Tag color="success">成功</Tag>
        <Tag color="processing">处理中</Tag>
        <Tag color="error">错误</Tag>
        <Tag color="warning">警告</Tag>
        <Tag color="default">默认</Tag>
        <Tag color="magenta">magenta</Tag>
        <Tag color="red">red</Tag>
        <Tag color="volcano">volcano</Tag>
        <Tag color="orange">orange</Tag>
        <Tag color="gold">gold</Tag>
        <Tag color="lime">lime</Tag>
        <Tag color="green">green</Tag>
        <Tag color="cyan">cyan</Tag>
        <Tag color="blue">blue</Tag>
        <Tag color="geekblue">geekblue</Tag>
        <Tag color="purple">purple</Tag>
      </Space>
      {/* Select 带选项/箭头/选中项 + large —— 注入 ant-select-show-arrow/selection-item/lg */}
      <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
        <Select defaultValue="a" style={{ width: 200 }} options={[{ value: 'a', label: '选项 A' }, { value: 'b', label: '选项 B' }]} />
        <Select size="large" style={{ width: 200 }} options={[{ value: 'a', label: '大号' }]} />
        <Select defaultValue="a" size="small" style={{ width: 120 }} options={[{ value: 'a', label: '小号' }]} />
      </div>
      {/* Avatar 变体 —— 注入 ant-avatar-circle/square/icon */}
      <Space style={{ marginTop: 8 }}>
        <Avatar>圆</Avatar>
        <Avatar shape="square">方</Avatar>
        <Avatar size="large">大</Avatar>
        <Avatar size="small">小</Avatar>
      </Space>
      {/* Statistic 带前后缀 —— 注入 ant-statistic-content-value-int/-prefix/-suffix */}
      <Card style={{ marginTop: 8 }}><Statistic title="金额" value={12345} prefix="¥" suffix="元" /></Card>
      {/* Pagination 带分页项 —— 注入 ant-pagination-item/prev/next 等 */}
      <Pagination defaultCurrent={1} total={50} style={{ marginTop: 8 }} />
      {/* Modal open —— portal 到 body，cssinjs 注入全量 ant-modal-* 样式（CSS 入 head 即被提取，DOM 不入展厅） */}
      <Modal open title="弹窗标题" okText="确定" cancelText="取消">
        <p>弹窗内容</p>
      </Modal>
      {/* Drawer open —— 注入 ant-drawer-* */}
      <Drawer open title="抽屉">抽屉内容</Drawer>
    </div>
  ),
};

// ---- 3. 展厅：happy-dom 真实渲染一次 → flushSync 跑 effect → 提取 head <style> + 展厅 DOM ----
const container = doc.createElement('div');
doc.body.appendChild(container);
const Gallery: React.FC = () => (
  <ConfigProvider theme={theme}>
    <div>{Object.entries(components).map(([name, el]) => (
      <section key={name} style={{ margin: '24px 0', padding: 24, border: '1px solid #f0f0f0', borderRadius: 8 }}>
        <h3 style={{ margin: '0 0 16px', color: '#595959' }}>{name}</h3>
        {el}
      </section>
    ))}</div>
  </ConfigProvider>
);
const root = createRoot(container);
flushSync(() => { root.render(<Gallery />); });
await new Promise((r) => setTimeout(r, 300));
// 展厅 DOM + <style> 必须在 unmount 前取——unmount 会清空 container 并触发 cssinjs 清理组件 token 变量所在的 <style> 块，
// 若在 unmount 后提取，会丢失全部组件级 token 定义（--ant-menu-* / --ant-btn-* / --ant-table-* 等 ~355 个），
// 只剩选择器规则（var() 引用空变量）→ 菜单/按钮等组件视觉全失效。
const galleryHtml = container.innerHTML;
const styleEls = doc.querySelectorAll('style');
// post-process：把 cssVar key:'root' 产生的 .root scope 全局化成 :root，agent 直接 :root 覆盖变量值，不需在产物挂特殊 class。
// ⚠ scoped 组件 token 块必须全局化（首版 bug：只 replace '.root{' 漏了 '.root.ant-menu-css-var{' 等 scoped 块）。
//   antd cssinjs 把全局 seed token 注入 .root{...}，但把组件级 token（--ant-menu-* / --ant-btn-* 等）注入
//   .root.ant-xxx-css-var{...} scoped 块（需元素同时带 root + ant-xxx-css-var 类才匹配）。
//   静态 HTML 不挂这些类 → scoped 组件 token 永不定义 → var(--ant-menu-item-height) 等解析失败 →
//   菜单 height 塌 0、color fallback 黑色 → 深底黑字不可见 = "侧栏菜单没了"。根因从首版 build 就在。
// 修复：所有 .root 及其 scoped 组合（.root.ant-menu-css-var{ / .root .xxx{ / .root{）全部 → :root，让组件级 token 全局生效。
const rawCss = [...styleEls].map((s) => s.textContent || '').filter(Boolean).join('\n');
const css = rawCss
  .replace(/\.root(?=\.[a-z0-9-])/g, ':root')      // .root.xxx → :root.xxx
  .replace(/:root(\.[a-z0-9-]+)+\{/g, ':root{')   // :root.ant-menu-css-var{ → :root{（scoped 组件 token 块全局化）
  .replace(/\.root\{/g, ':root{')                  // 单独 .root{ → :root{（全局 seed token 块）
  .replace(/\.root(?=[ #.>~+])/g, ':root')         // 后代选择器 .root .xxx → :root .xxx
  .replace(/\.root$/, ':root');                    // 行末残留
root.unmount();

// ---- 4. 片段 DOM：renderToStaticMarkup（纯 DOM，快，class 与展厅一致因 hashed:false）----
function renderFrag(el: React.ReactElement): string {
  return renderToStaticMarkup(<ConfigProvider theme={theme}>{el}</ConfigProvider>);
}

// ---- 5. 输出 ----
const outDir = path.resolve(__dirname, '../skills/product/ui-prototype-gen/templates/prototype-skeleton');
const fragDir = path.join(outDir, 'fragments');
fs.mkdirSync(fragDir, { recursive: true });

fs.writeFileSync(path.join(outDir, 'antd.static.css'), css, 'utf8');
// coverage 是 CSS 注入覆盖矩阵（含 Modal/Drawer portal），只在展厅渲染（步骤3 flushSync 客户端渲染，支持 portal）；
// 不走 renderToStaticMarkup 片段循环——server renderer 不支持 portal 会崩，且它本就不是可复用片段。
for (const [name, el] of Object.entries(components)) {
  if (name === 'coverage') continue;
  fs.writeFileSync(path.join(fragDir, `${name}.html`), renderFrag(el), 'utf8');
}

const indexHtml = `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>antd5 预构建起手包 · 组件展厅</title>
<link rel="stylesheet" href="antd.static.css">
</head>
<body>
<div style="max-width:1200px;margin:0 auto;padding:24px">
<h1 style="font-size:24px;margin:0 0 8px">antd5 预构建起手包 · 组件展厅</h1>
<p style="color:#8c8c8c;margin:0 0 24px">cssVar:{key:'root'} + hashed:false · 商务高密度主色 #1668DC · 双击静态查看</p>
${galleryHtml}
</div>
</body>
</html>`;
fs.writeFileSync(path.join(outDir, 'index.html'), indexHtml, 'utf8');

const cssVarHit = (css.match(/--ant-[a-z0-9-]+/g) || []).length;
const scopeHit = (css.match(/\.css-var-[a-z0-9-]+/g) || []).length;
const rootHit = (css.match(/:root\s*{/g) || []).length;
console.log('[build] antd.static.css =', (css.length / 1024).toFixed(1), 'KB');
console.log('[build] fragments =', Object.keys(components).length, '个 →', fragDir);
console.log('[build] index.html =', (indexHtml.length / 1024).toFixed(1), 'KB');
console.log('[build] head <style> 数量:', styleEls.length);
console.log('[build] cssVar 变量命中 --ant-*:', cssVarHit, '个');
console.log('[build] .css-var-* scope 命中:', scopeHit, '| :root{ 命中:', rootHit);
console.log('[build] 输出目录:', outDir);
