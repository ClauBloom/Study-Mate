# 线性代数 Resources

> 定位：**延伸阅读 + 易变内容的核对来源**，不是「知识来源清单」——稳定的定义与定理模型已经掌握，
> 这里只放两类东西：某一课想再听一遍别人怎么讲的；以及屏幕上的名词（库的函数名、软件版本）需要核对时去哪儿查。

## Knowledge

- [3Blue1Brown · 线性代数的本质（中文配音版）](https://www.3blue1brown.com/topics/linear-algebra)
  一行说明：整套动画把「向量、线性变换、矩阵乘法、特征向量」画成可看的几何过程；第 1 课讲向量与
  线性组合、第 3 课讲矩阵即变换，看课件卡在几何图像上时用它换一个讲法。
- [MIT 18.06 Linear Algebra（Gilbert Strang，Spring 2010）](https://ocw.mit.edu/courses/18-06sc-linear-algebra-fall-2011/)
  一行说明：MIT 的本科线代公开课，讲稿、习题与视频齐全。第 1 讲消元的几何、第 5~9 讲列空间与零空间、
  第 21~22 讲特征值，都对应本课节点。它的顺序是先讲消元再讲向量空间，与本大纲相反——用来补推导，不用来排顺序。
- [3Blue1Brown · 线性变换与矩阵](https://www.3blue1brown.com/lessons/linear-transformations)
  一行说明：把「矩阵的每一列是基向量变换后的落点」这件事画出来的那一集，配合本课第 2 课的示意图看。
- [3Blue1Brown · 线性组合、张成与基向量](https://www.3blue1brown.com/lessons/span)
  一行说明：线性无关与张成的几何版解释，第 1 课的延伸；看完能自己判断三个三维向量是不是共面。
- [Mathematics for Machine Learning（Deisenroth 等，剑桥大学出版社）](https://mml-book.github.io/)
  一行说明：机器学习的数学教材，官方 PDF 免费。第 2~4 章覆盖本课范围，书里的记号偏工程、很少讲几何，
  适合当作「看教材里的符号长什么样」的对照读物。
- [SymPy 官方文档 · 线性代数模块](https://docs.sympy.org/latest/modules/matrices/matrices.html)
  一行说明：需要核对现成库怎么表示矩阵、怎么算阶梯形时的官方来源。注意版本差异：`rref()` 返回的是
  `(矩阵, 主元列下标)` 二元组，这个返回值在不同大版本间改过。
- [NumPy 官方文档 · `numpy.linalg`](https://numpy.org/doc/stable/reference/routines.linalg.html)
  一行说明：核对 `solve` / `matrix_rank` / `eig` 的准确签名与异常类型；`LinAlgError` 的触发条件是
  易变内容（不同版本对奇异矩阵的判定宽容度不一样），以这个页面为准。
- [Python 官方文档 · `fractions.Fraction`](https://docs.python.org/zh-cn/3/library/fractions.html)
  一行说明：本课 lab 用分数做精确消元的依据；核对 `Fraction` 与整数、浮点数混算时的行为。

## Wisdom (Communities)

- [Mathematics Stack Exchange · linear-algebra 标签](https://math.stackexchange.com/questions/tagged/linear-algebra)
  一行说明：拿一个具体的矩阵或方程组去问「为什么这样消元会改变解集」这类问题；提问时把矩阵原样贴出来，
  比描述更快得到回答。
- [3Blue1Brown 的 Reddit 社区 r/3Blue1Brown](https://www.reddit.com/r/3blue1brown/)
  一行说明：看到某集动画里一步跳过去了、想找别人补的中间推导时用；提问前先搜，几何直观的问题重复率很高。

## Gaps

- 没有找到「以图像压缩为线索讲特征分解」的高质量中文材料：第 5 课要用的真实过程例子，目前只能拿
  人口迁移这类离散迭代自己造数据，图像压缩那侧还缺一个能跑、能看的样例。
- 手写消元的排错材料（人工消元常错在哪、怎么自检）没有权威来源，本课的自检清单是自己总结的，
  以后找到教材里的对应小节再替换。
