<template>
  <div class="common-layout">
    <el-container class="layout-container">
      <el-aside width="220px" class="aside">
        <div class="logo">
          <h2>🛡️ 大模型智能安全网关</h2>
        </div>
        <el-menu
          router
          :default-active="$route.path"
          class="el-menu-vertical-demo"
          background-color="#1e1e2d"
          text-color="#b0b0c0"
          active-text-color="#ffffff"
        >
          <el-menu-item index="/">
            <el-icon><Odometer /></el-icon>
            <span>仪表盘</span>
          </el-menu-item>
          <el-menu-item index="/chat">
            <el-icon><ChatDotRound /></el-icon>
            <span>对话游乐场</span>
          </el-menu-item>
          <el-menu-item index="/policy">
            <el-icon><Setting /></el-icon>
            <span>策略配置</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <el-container>
        <el-header class="header">
          <div class="header-content">
            <h3>{{ $route.name }}</h3>
          </div>
        </el-header>
        <el-main class="main">
          <div class="content-wrapper">
             <router-view v-slot="{ Component }">
              <transition name="fade" mode="out-in">
                <component :is="Component" />
              </transition>
            </router-view>
          </div>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<style scoped>
.layout-container {
  height: 100vh;
}

.aside {
  background-color: #1e1e2d;
  color: white;
  display: flex;
  flex-direction: column;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #2b2b40;
}

.logo h2 {
  font-size: 16px;
  margin: 0;
  color: #fff;
}

.el-menu {
  border-right: none;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.main {
  background-color: #f5f7fa;
  padding: 20px;
}

.content-wrapper {
  background: white;
  padding: 20px;
  border-radius: 8px;
  height: calc(100vh - 140px); /* Fixed height for sticky layout */
  overflow: auto;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  display: flex;       /* Add flex to support children filling height */
  flex-direction: column;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
