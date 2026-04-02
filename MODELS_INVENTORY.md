# Homeworld Project: Model Assets Inventory

This document provides a summary of the 3D assets available for the "Homeworld" project. These assets are categorized by their function and file format suitability for browser-based development.

## 📂 Available Categories
- **Animals**: Various creatures.
- **Blocks**: Standard building blocks (Dirt, Grass, Stone, Crate, etc.).
- **Characters**: Humanoids or main entities.
- **Enemies**: Fantasy-themed monsters (Giant, Orc, Skeleton, Zombie, etc.).
- **Environment**: Foliage, rocks, chests, fences, and decorative items.
- **Pixel Blocks**: Stylized low-resolution blocks.
- **Tools**: Equipment and interactive items.

---

## 🏗️ Technical Specification & Browser Suitability

For a browser-based game (using engines like **Three.js**, **Babylon.js**, or **PlayCanvas**), the following formats are available:

| Format | File Extension | Web Suitability | Recommendation |
| :--- | :--- | :--- | :--- |
| **glTF** | `.gltf` | ⭐⭐⭐⭐⭐ (Excellent) | **Primary Choice**. Optimized for the web, supports materials, textures, and animations natively. |
| **FBX** | `.fbx` | ⭐⭐⭐ (Good) | Can be used with Three.js `FBXLoader`, but files are often larger. Best converted to glTF/glb for production. |
| **OBJ/MTL** | `.obj`, `.mtl` | ⭐⭐ (Fair) | Simple but does not support animations well. Material definitions are separate (.mtl). |
| **Blender** | `.blend` | ❌ (None) | Native project files. Must be exported to glTF or FBX before they can be used in a browser. |

---

## 📋 Folder Summary

| Category | glTF Support | Notes |
| :--- | :---: | :--- |
| **Animals** | ✅ | Includes various creature models. |
| **Blocks** | ✅ | Dirt, Grass, Stone, Crate, Ice, Snow, etc. |
| **Characters** | ✅ | Main humanoid models with animation potential. |
| **Enemies** | ✅ | Wizard, Skeleton, Goblin, Yeti, Demon, etc. |
| **Environment** | ✅ | Tree, Rock, Fence, Key, Chest, Lever, etc. |
| **Pixel Blocks**| ✅ | Stylized cubes for a voxel-like feel. |
| **Tools** | ✅ | Functional items for the player. |

---

## 🚀 Recommendation for Start
We should prioritize using the **`.gltf`** files located in each category's `glTF/` subfolder. They are ready to be loaded by a web browser without additional conversion.

*Feel free to modify this description as we define our project scope.*

this is going  to mmorpg game with postgresql database and nodejs backend and threejs frontend.
database is going to be base on postgresql on the same server
user  accounts are stored in postgres database named homeserver. table public.users
session token should exist to run the game. check implementation for security for homeserver site (local server)

user can move around the world and interact with objects and other users. we should have day night cycle. 
create a world with different biomes (we should have at least grass, forest, lake, mountain biomes. give ideas for more biomes) and environments. use vegetation  models from environment folder. use blocks from blocks folder. use pixel blocks from pixel blocks folder. use rocks from environment folder. use blocks for creating terrain from models in blocks folder. 
create a character for the user. user should be able to select character when enters game. character models are in characters folder. 
create a inventory for the user. inventory is stored in postgres database named homeserver. table public.inventory

this is for later implementation

create a crafting system for the user.
create a quest system for the user.
create a combat system for the user.
create a trading system for the user.
create a guild system for the user.
create a chat system for the user.
create a friends system for the user.
create a mail system for the user.
create a party system for the user.
create a pet system for the user.
create a mount system for the user.
create a skill system for the user.
create a talent system for the user.
create a achievement system for the user.
create a title system for the user.
create a reputation system for the user.
create a title system for the user.
