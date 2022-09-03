#!/usr/bin/env python3

# ATENÇÃO: NENHUM IMPORT ADICIONAL É PERMITIDO!
import sys
import math
import base64
import tkinter
from io import BytesIO
from PIL import Image as PILImage


def criar_kernel_desfoque(n):
    kernel = [[1 / (n**2) for _ in range(n)] for _ in range(n)]
    return kernel


class Imagem:
    def __init__(self, largura, altura, pixels):
        self.largura = largura
        self.altura = altura
        self.pixels = pixels

    def get_pixel(self, x, y):
        if x < 0:
            x = 0
        elif x >= self.largura:
            x = self.largura - 1
        if y < 0:
            y = 0
        elif y >= self.altura:
            y = self.altura - 1

        return self.pixels[(x + y * self.largura)]

    def set_pixel(self, x, y, c):
        self.pixels[(x + y * self.largura)] = c

    def aplicar_por_pixel(self, func):
        resultado = Imagem.new(self.largura, self.altura)
        for x in range(resultado.largura):
            for y in range(resultado.altura):
                cor = self.get_pixel(x, y)
                nova_cor = func(cor)
                resultado.set_pixel(x, y, nova_cor)

        return resultado

    def tratar(self):  # função que pega
        for x in range(self.largura):
            for y in range(self.altura):
                pix = self.get_pixel(x, y)
                if pix < 0:
                    pix = 0
                elif pix > 255:
                    pix = 255
                self.set_pixel(x, y, int(round(pix)))

    def correlation(self, kn):  # A função 'correlation' que aplica o kernel na imagem
        k = len(kn)
        centro = k // 2
        final_img = Imagem.new(self.largura, self.altura)  # Criar uma imagem em branco com a largura e altura da imagem base

        for x in range(final_img.largura):
            for y in range(final_img.altura):
                novcor = 0
                for w in range(k):
                    for h in range(k):
                        x1 = x - centro + h
                        y1 = y - centro + w
                        novcor += self.get_pixel(x1, y1) * kn[w][h]

                final_img.set_pixel(x, y, novcor)

        return final_img

    def invertido(self):
        return self.aplicar_por_pixel(lambda c: 255 - c)

    def borrado(self, n):
        kernel = criar_kernel_desfoque(n)
        im = self.correlation(kernel)
        im.tratar()
        return im

    def focado(self, n):
        borra = self.borrado(n)
        S = Imagem.new(self.largura, self.altura)
        for x in range(self.largura):
            for y in range(self.altura):
                pxl = round(2*self.get_pixel(x, y) - borra.get_pixel(x, y))
                S.set_pixel(x, y, pxl)
        S.tratar()
        return S

    def bordas(self):
        S = Imagem.new(self.largura, self.altura)
        k1 = self.correlation([[-1, 0, 1],
                                [-2, 0, 2],
                                [-1, 0, 1]])
        k2 = self.correlation([[-1, -2, -1],
                                [0, 0, 0],
                                [1, 2, 1]])

        for x in range(self.largura):
            for y in range(self.altura):
                pxl = round(math.sqrt((k1.get_pixel(x, y)**2) + k2.get_pixel(x, y)**2))
                S.set_pixel(x, y, pxl)
        S.tratar()
        return S

    # Abaixo deste ponto estão utilitários para carregar, salvar,
    # mostrar e testar imagens.

    def __eq__(self, other):
        return all(getattr(self, i) == getattr(other, i)
                   for i in ('altura', 'largura', 'pixels'))

    def __repr__(self):
        return "Imagem(%s, %s, %s)" % (self.largura, self.altura, self.pixels)

    @classmethod
    def carregar(cls, arquivo):
        """
        Carrega uma imagem a partir de um arquivo e retorna uma instância
        da classe representando essa imagem. Também realiza a conversão
        para escala de cinza.

        Modo de usar:
           i = Imagem.carregar('imagens_teste/gato.png')
        """
        with open(arquivo, 'rb') as img_handle:
            img = PILImage.open(img_handle)
            img_data = img.getdata()
            if img.mode.startswith('RGB'):
                pixels = [round(.299 * p[0] + .587 * p[1] + .114 * p[2]) for p in img_data]
            elif img.mode == 'LA':
                pixels = [p[0] for p in img_data]
            elif img.mode == 'L':
                pixels = list(img_data)
            else:
                raise ValueError('Modo de imagem não suportado: %r' % img.mode)
            w, h = img.size
            return cls(w, h, pixels)

    @classmethod
    def new(cls, largura, altura):
        """
        Cria uma nova imagem em branco (tudo 0) para uma dada largura e altura.

        Modo de uso:
            i = Imagem.new(640, 480)
        """
        return cls(largura, altura, [0 for i in range(largura * altura)])

    def salvar(self, arquivo, modo='PNG'):
        """
        Salva uma dada imagem no disco ou para um objeto semelhante a um
        arquivo. Se "arquivo" é dado como uma string, o tipo de arquivo
        será inferido do próprio nome. Se "arquivo" for dado como um
        objeto semelhante a um arquivo, o tipo de arquivo será determinaddo
        pelo parâmetro "modo".
        """
        out = PILImage.new(mode='L', size=(self.largura, self.altura))
        out.putdata(self.pixels)
        if isinstance(arquivo, str):
            out.save(arquivo)
        else:
            out.save(arquivo, modo)
        out.close()

    def gif_data(self):
        """
        Retorna uma string codificada em base 64, contendo
        a imagem como um GIF. É um utilitário para fazer a função
        mostrar ficar mais limpa.
        """
        buff = BytesIO()
        self.salvar(buff, modo='GIF')
        return base64.b64encode(buff.getvalue())

    def mostrar(self):
        """
        Mostra a imagem em uma janela Tk.
        """
        global WINDOWS_OPENED
        if tk_root is None:
            # Se o Tk não está inicializado de forma apropriada, não faz nada.
            return
        WINDOWS_OPENED = True
        toplevel = tkinter.Toplevel()
        # highlightthickness=0 é um hack para evitar que o redimensionamento da janela
        # dispare outro evendo de redimensionamento (causando um loop infinito). Veja
        # https://stackoverflow.com/questions/22838255/tkinter-canvas-resizing-automatically
        canvas = tkinter.Canvas(toplevel, height=self.altura,
                                width=self.largura, highlightthickness=0)
        canvas.pack()
        canvas.img = tkinter.PhotoImage(data=self.gif_data())
        canvas.create_image(0, 0, image=canvas.img, anchor=tkinter.NW)

        def on_resize(event):
            # Realiza o redimensionamento da imagem quando a janela é redimensionada.
            # O procedimento é:
            #  * Converter para uma imagem PIL
            #  * Redimensionar essa imagem
            #  * Obter o GIF codificado em base64 a partir da imagem redimensionada
            #  * Colocar essa imagem em um label tkinter
            #  * Mostrar essa imagem no canvas
            new_img = PILImage.new(mode='L', size=(self.largura, self.altura))
            new_img.putdata(self.pixels)
            new_img = new_img.resize((event.width, event.height), PILImage.NEAREST)
            buff = BytesIO()
            new_img.save(buff, 'GIF')
            canvas.img = tkinter.PhotoImage(data=base64.b64encode(buff.getvalue()))
            canvas.configure(height=event.height, width=event.width)
            canvas.create_image(0, 0, image=canvas.img, anchor=tkinter.NW)

        # Finalmente, vincular essa função para que ela seja chamada
        # quando a janela for redimensionada.
        canvas.bind('<Configure>', on_resize)
        toplevel.bind('<Configure>', lambda e: canvas.configure(height=e.height, width=e.width))

        # when the window is closed, the program should stop
        toplevel.protocol('WM_DELETE_WINDOW', tk_root.destroy)


try:
    tk_root = tkinter.Tk()
    tk_root.withdraw()
    tcl = tkinter.Tcl()


    def reafter():
        tcl.after(500, reafter)


    tcl.after(500, reafter)
except:
    tk_root = None
WINDOWS_OPENED = False

if __name__ == '__main__':
    # O código neste bloco somente será rodado quando você, explicitamente,
    #  rodar o seu script, e não quando os testes forem executados. Este é um
    #  bom lugar para gerar imagens, etc.
    pass
    # Questão 2 — Peixe inverido
    # im = Imagem.carregar('imagens_teste/peixe.png') # função para carregar a imagem do peixe e colocar na variável "im"
    # x = im.invertido()                              # função para inverter a imagem carregada na função anterior e colocar na variável "x"
    # x.salvar('imagens_salvas/peixe.png')            # função para salvar a imagem invertida

    # Questão 4 — Imagem do porco empurrado para a direita
    # im = Imagem.carregar('imagens_teste/porco.png')
    # kernel = [[0, 0, 0, 0, 0, 0, 0, 0, 0],
    #          [0, 0, 0, 0, 0, 0, 0, 0, 0],
    #          [1, 0, 0, 0, 0, 0, 0, 0, 0],
    #          [0, 0, 0, 0, 0, 0, 0, 0, 0],
    #          [0, 0, 0, 0, 0, 0, 0, 0, 0],
    #          [0, 0, 0, 0, 0, 0, 0, 0, 0],
    #          [0, 0, 0, 0, 0, 0, 0, 0, 0],
    #          [0, 0, 0, 0, 0, 0, 0, 0, 0],
    #          [0, 0, 0, 0, 0, 0, 0, 0, 0]]
    # x = im.correlation(kernel)
    # x.salvar('imagens_salvas/porco.png')
    # x.mostrar()
    # im.mostrar()

    # Questão Gato Borrado
    # im = Imagem.carregar('imagens_teste/gato.png')
    # im1 = im.borrado(5)
    # im1.salvar('imagens_salvas/gato.png')
    # im1.mostrar()
    # im.mostrar()

    # Questão 5
    # im = Imagem.carregar('imagens_teste/python.png')
    # im1 = im.focado(11)
    # im1.salvar('imagens_salvas/python.png')
    # im1.mostrar()
    # im.mostrar()

    # Questão 6
    # im = Imagem.carregar('imagens_teste/obra.png')
    # im1 = im.bordas()
    # im1.salvar('imagens_salvas/obra.png')
    # im.mostrar()
    # im1.mostrar()
    # O código a seguir fará com que as janelas em Imagem.show
    # sejam mostradas de modo apropriado, se estivermos rodando
    # interativamente ou não:
    if WINDOWS_OPENED and not sys.flags.interactive:
        tk_root.mainloop()