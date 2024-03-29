### 解题思路
两个节点p和q的最近公共祖先，要么是p或者q本身，要么是某节点node，p和q分别在node的左右（右左）子树中。后序遍历，分别求得左右子树中的最近公共祖先，如果left是空，right不为空，说明最近公共祖先在右子树中，right即为右子树中最近公共祖先。反之，left是左子树中的最近公共祖先。当left和right均不为空，说明p和q在当前节点的左右（右左）子树中，当前节点node即为最近公共祖先，直接返回当前节点node。

递归边界是到达叶子节点要返回，到达p，q要返回。最近公共祖先不会在p和q的子节点中，所以碰到直接返回。
### 复杂度分析
**时间复杂度**：$O(N)$。N为二叉树的节点个数。

**空间复杂度**：$O(h)$。h为树高。递归深度最深为树高。

### 解题代码
```python
# Definition for a binary tree node.
# class TreeNode:
#     def __init__(self, x):
#         self.val = x
#         self.left = None
#         self.right = None

class Solution:
    def lowestCommonAncestor(self, root: TreeNode, p: TreeNode, q: TreeNode) -> TreeNode:
        if root is None or root == p or root == q: 
            return root
        left = self.lowestCommonAncestor(root.left, p, q)
        right = self.lowestCommonAncestor(root.right, p, q)
        if left is None:
            return right
        elif right is None:
            return left
        else:
            return root
```