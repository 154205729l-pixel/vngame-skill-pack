# Image 2 提示词规则

## 通用规则

- 使用用户提供图作为 composition/reference 时，保留镜头角度、人物位置和运动关系。
- 替换真实队徽、广告、球衣标识、可识别人脸和现实文字。
- 奖杯只做无标识艺术化道具，不出现官方铭文。
- 画面提示词中明确写：no logos, no team badges, no brand marks, no sponsor boards, no readable real club names, no real player likeness.

## 画风可复用模板

```text
animated comic-book feature film look, inspired by dynamic multiverse superhero animation, stylized 3D characters with 2D comic overpaint, bold graphic shapes, expressive oversized eyes, exaggerated facial expressions, childlike proportions, painterly brush strokes, halftone dots, offset-print texture, inked shadow hatching, rim light color blocks, energetic camera angles, cinematic depth, bright suspense rather than horror.
```

## 儿童 IP 人物规则

```text
ALL human characters must be children aged 8-12. No adults anywhere. No adult body proportions, no facial hair, no adult muscles, no mature faces.
```

## 每章末尾要写

- 通用风格
- 人物锚定
- 场景图列表
- 图生图参考规则
- 版权规避约束

## 请求方式约束

- 图片生成统一走 FlashAPI 兼容入口，不要改写成 OpenAI OpenAPI 直连。
- 文生图固定使用 `POST https://ai.flashapi.top/v1/images/generations`。
- 图生图固定使用 `POST https://ai.flashapi.top/v1/images/edits`。
- 鉴权优先读取 `FLASHAPI_KEY`，没有时才退到 `OPENAI_API_KEY`。

## 画风参考与人物锚定分离

- 用户说“参考某游戏画风”时，只继承画风、构图语言、光影和质感，不继承该游戏主角的肤色、发型、身份或号码。
- 体育人物儿童化时要单独写人物锚定：例如哈兰德型是金发、可丸子头、高个结实；厄德高型是浅棕/金棕发、清瘦、安静队长气质。
- 群像提示词必须避免克隆：只允许最近/主角具备明确明星锚定，其余孩子写“varied hairstyles, varied faces, different Nordic boys”。
- 队服或战袍要写明真实规避和设计方向：无队徽、无赞助商、无可读文字；可用红底、蓝白细节、维京披风/皮革/毛边做原创表达。
