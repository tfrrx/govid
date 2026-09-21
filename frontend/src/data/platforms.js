/**
 * 平台墙数据。
 * 有意不使用第三方品牌 Logo 图片：一是不引外链资源，二是避免图形失真。
 * 统一用「品牌色圆角块 + 品牌首字 / 缩写」的视觉语言，风格一致且不会画错。
 *
 * 口径说明：这里列的是 yt-dlp 官方具备解析器的平台，即「理论支持」。
 * 实际成功率受登录态与源站接口变动影响，实测矩阵见 docs/03-平台支持矩阵.md。
 */
export const PLATFORMS = [
  { name: 'YouTube', color: '#FF0000', mark: 'YT' },
  { name: '哔哩哔哩', color: '#00A1D6', mark: '哔' },
  { name: 'Vimeo', color: '#1AB7EA', mark: 'V' },
  { name: 'TikTok', color: '#111111', mark: 'TT' },
  { name: 'X', color: '#111111', mark: 'X' },
  { name: 'Instagram', color: '#E1306C', mark: 'IG' },
  { name: 'Facebook', color: '#1877F2', mark: 'f' },
  { name: 'Twitch', color: '#9146FF', mark: 'Tw' },
  { name: '抖音', color: '#111111', mark: '抖' },
  { name: '优酷', color: '#118EE9', mark: '优' },
  { name: '腾讯视频', color: '#FF6000', mark: '腾' },
  { name: '爱奇艺', color: '#00C55A', mark: '爱' },
  { name: '微博', color: '#E6162D', mark: '微' },
  { name: '小红书', color: '#FF2442', mark: '红' },
  { name: 'Reddit', color: '#FF4500', mark: 'R' },
  { name: 'Dailymotion', color: '#00AAFF', mark: 'd' },
  { name: 'SoundCloud', color: '#FF5500', mark: 'S' },
  { name: 'TED', color: '#E62B1E', mark: 'TED' },
  { name: 'niconico', color: '#231815', mark: 'n' },
  { name: 'AcFun', color: '#FD4C5B', mark: 'A' },
]

export const PLATFORM_ROWS = [PLATFORMS.slice(0, 10), PLATFORMS.slice(10)]
