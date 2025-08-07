// characterPresets.js
import * as PIXI from 'pixi.js';

/**
 * 工厂函数：创建带自绘制方法的角色对象
 * @param {Object} options - 角色属性（如 name、性别、发型等）
 * @returns {Object} 封装角色属性和 createContainer 方法的对象
 */
function createCharacter(options) {
  return {
    ...options,

    /**
     * 生成 PixiJS 角色容器（可直接添加到 stage）
     * @returns {PIXI.Container}
     */
    createContainer() {
      const container = new PIXI.Container();

      // 头部
      const head = new PIXI.Graphics();
      head.beginFill(0xFFD580);
      head.drawCircle(0, 0, 50);
      head.endFill();
      container.addChild(head);

      // 身体
      const body = new PIXI.Graphics();
      body.beginFill(parseInt(this.clothesColor.replace('#', '0x')));
      body.drawRect(-30, 50, 60, 80);
      body.endFill();
      container.addChild(body);

      // 发型
      const hair = new PIXI.Graphics();
      hair.beginFill(parseInt((this.hairColor || "#222222").replace('#', '0x')));
      hair.drawEllipse(0, -30, 45, 20);
      hair.endFill();
      container.addChild(hair);

      // 左眼
      const leftEye = new PIXI.Graphics();
      leftEye.beginFill(0x333333);
      leftEye.drawCircle(-15, -10, 6);
      leftEye.endFill();
      container.addChild(leftEye);

      // 右眼
      const rightEye = new PIXI.Graphics();
      rightEye.beginFill(0x333333);
      rightEye.drawCircle(15, -10, 6);
      rightEye.endFill();
      container.addChild(rightEye);

      // 嘴巴
      const mouth = new PIXI.Graphics();
      mouth.lineStyle(3, 0x992200);
      mouth.moveTo(-12, 18);
      mouth.quadraticCurveTo(0, 28, 12, 18);
      container.addChild(mouth);

      // 可以拓展其它配件、换装等
      return container;
    }
  }
}

// 导出角色数组（每个角色都带 createContainer 方法和属性）
export const characterPresets = [
  createCharacter({
    name: "小明",
    gender: "male",
    hair: "短发",
    personality: "温和",
    background: "平民",
    clothesColor: "#4582EC",
    hairColor: "#222222"
  }),
  createCharacter({
    name: "阿兰",
    gender: "female",
    hair: "长发",
    personality: "外向",
    background: "贵族",
    clothesColor: "#D55C5A",
    hairColor: "#885522"
  }),
  createCharacter({
    name: "青云",
    gender: "male",
    hair: "马尾",
    personality: "谨慎",
    background: "武者",
    clothesColor: "#3A9B56",
    hairColor: "#334488"
  })
];
