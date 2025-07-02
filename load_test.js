
const { chromium } = require('playwright');
async function loadTest() {
    const browsers = [];
    const pages = [];
    
    // 10개 동시 브라우저 인스턴스
    for (let i = 0; i < 10; i++) {
        const browser = await chromium.launch();
        const page = await browser.newPage();
        browsers.push(browser);
        pages.push(page);
    }
    
    const startTime = Date.now();
    
    // 동시 페이지 로드
    await Promise.all(pages.map(page => 
        page.goto('http://localhost:3000')
    ));
    
    const loadTime = Date.now() - startTime;
    
    // 정리
    await Promise.all(browsers.map(browser => browser.close()));
    
    console.log(JSON.stringify({
        concurrent_users: 10,
        total_load_time: loadTime,
        avg_load_time_per_user: loadTime / 10
    }));
}
loadTest();
