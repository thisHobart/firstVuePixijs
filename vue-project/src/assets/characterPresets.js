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
      head.beginFill(0xFFD580); // Skin color
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

      // 名字和称号
      const nameText = new PIXI.Text(this.name, { fontSize: 20, fill: 0xffffff, align: 'center' });
      nameText.anchor.set(0.5);
      nameText.y = 140;
      container.addChild(nameText);

      const titleText = new PIXI.Text(`(${this.title})`, { fontSize: 16, fill: 0x89dd7c, align: 'center' });
      titleText.anchor.set(0.5);
      titleText.y = 165;
      container.addChild(titleText);


      // 可以拓展其它配件、换装等
      return container;
    }
  }
}

// 导出角色数组（每个角色都带 createContainer 方法和属性）
export const characterPresets = [
  createCharacter({
    id: "player",
    name: "你",
    title: "新科状元",
    gender: "male",
    clothesColor: "#B22222", // Firebrick red for the player
    hairColor: "#000000"
  }),
  createCharacter({
    id: "emperor",
    name: "玄烨",
    title: "皇帝",
    gender: "male",
    clothesColor: "#FFFF00", // Bright yellow for emperor
    hairColor: "#111111"
  }),
  createCharacter({
    id: "minister",
    name: "张廷玉",
    title: "大臣",
    gender: "male",
    clothesColor: "#00008B", // Dark blue for minister
    hairColor: "#333333"
  }),
  createCharacter({
    id: "maid",
    name: "苏麻喇姑",
    title: "宫女",
    gender: "female",
    clothesColor: "#FFC0CB", // Pink for maid
    hairColor: "#444444"
  }),
  createCharacter({
    id: "eunuch",
    name: "李德全",
    title: "太监",
    gender: "male",
    clothesColor: "#808080", // Gray for eunuch
    hairColor: "#222222"
  })
];
