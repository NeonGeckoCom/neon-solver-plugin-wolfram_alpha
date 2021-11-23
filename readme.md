
Spoken answers api for wolfram alpha


```python
d = WolframAlphaSolver()
for sentence in d.spoken_answers("what is the speed of light"):
    print(sentence)
    # The speed of light has a value of about 300 million meters per second
```

Language support provided by language translation plugins

```python
d = WolframAlphaSolver()
for sentence in d.spoken_answers("qual é a velocidade da luz", lang="pt"):
    print(sentence)
    # A velocidade da luz tem um valor de cerca de 300 milhões de metros por segundo
```
