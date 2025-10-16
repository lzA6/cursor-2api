// 文件路径: app/providers/fetch_override.js

(function() {
    const originalFetch = window.fetch;

    window.fetch = new Proxy(originalFetch, {
        apply: async function(target, thisArg, args) {
            let [url, config] = args;

            if (typeof url === 'string' && url.includes('/api/chat') && config && config.method === 'POST') {
                console.log('Apollo Protocol: Intercepting fetch to /api/chat.');

                // --- 核心修改：使用从 Python 注入的、包含完整历史的 payload ---
                if (window.chatPayload) {
                    console.log('Apollo Protocol: Overriding request body with payload from Python.');
                    config.body = JSON.stringify(window.chatPayload);
                    // 更新 args[1] 以确保修改生效
                    args[1] = config;
                } else {
                    console.warn('Apollo Protocol: window.chatPayload not found. Using original request body.');
                }
                // --- 修改结束 ---

                try {
                    const response = await Reflect.apply(target, thisArg, args);

                    if (!response.ok) {
                        const errorText = await response.text();
                        const errorMessage = `Fetch failed via proxy: ${response.status} ${response.statusText}. Body: ${errorText}`;
                        if (window.onStreamError) window.onStreamError(errorMessage);
                        return new Response(errorText, { status: response.status, headers: response.headers });
                    }

                    if (!response.body) {
                        if (window.onStreamError) window.onStreamError('Response has no body');
                        return response;
                    }

                    const [streamForPython, streamForBrowser] = response.body.tee();

                    (async () => {
                        const reader = streamForPython.getReader();
                        const decoder = new TextDecoder();
                        try {
                            while (true) {
                                const { done, value } = await reader.read();
                                if (done) break;
                                const chunk = decoder.decode(value, { stream: true });
                                if (window.onStreamChunk) window.onStreamChunk(chunk);
                            }
                        } catch (e) {
                            if (window.onStreamError) window.onStreamError('Error reading stream: ' + e.toString());
                        } finally {
                            if (window.onStreamEnd) window.onStreamEnd();
                        }
                    })();
                    
                    return new Response(streamForBrowser, {
                        status: response.status,
                        statusText: response.statusText,
                        headers: response.headers,
                    });

                } catch (error) {
                    if (window.onStreamError) window.onStreamError(error.toString());
                    throw error;
                }
            }

            return Reflect.apply(target, thisArg, args);
        }
    });
})();
