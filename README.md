Example:

```
import sprintly

account = sprintly.Account(('foo@bar.com', 'cafebabefeeddeadbeefdefec8'))
product = account.products()[0]
item    = product.item('1')
comment = item.create_comment({ 'body': 'hello world!' })
comment1 = item.comments()[0]
comment2 = item.comment(comment.id)
```
