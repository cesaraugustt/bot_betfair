from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
import time
import os


URL = 'https://www.betfair.com/'
ODD_ALVO = 1.8
TEMPO_MAX = 35
VALOR_BET = 0.58


def carrega_credenciais():
    load_dotenv()
    email = os.getenv('EMAIL')
    senha = os.getenv('SENHA')

    if not email or not senha:
        print('Credenciais de login ausentes no arquivo .env.')

    return email, senha


def aceita_cookies(driver):
    try:
        time.sleep(2)
        # botão aceita apenas cookies necessários
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.ID, 'onetrust-reject-all-handler'))).click()
        print('Cookies aceitos.')

    except TimeoutException:
        print('Botão de cookies não encontrado.')


def login(driver, email, senha):
    try:
        driver.find_element(By.ID, 'ssc-liu').send_keys(email)
        driver.find_element(By.ID, 'ssc-lipw').send_keys(senha)
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'ssc-lis'))).click()
        print('Login realizado.')

    except TimeoutException:
        print('Erro ao realizar login.')


def verifica_tempo(driver):
    try:
        tempo_elemento = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, '_2MTBZ')))
        minutos = int(tempo_elemento.text.replace("'", ""))

        if minutos > TEMPO_MAX:
            print('Tempo máximo atingido.')
            return True, minutos

        else:
            return False, minutos

    except NoSuchElementException:
        print('Elemento de tempo não encontrado.')
        return False, None

    except ValueError as e:
        print(f'Erro ao converter tempo: {e}')
        return False, None


def verifica_placar(driver):
    try:
        placar_casa = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='_3zclL']//div[1]"))).text.strip()
        placar_fora = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='_2v7CY PuNpm']//div[2]"))).text.strip()
        print(f'Placar: {placar_casa} x {placar_fora}')

        if placar_casa != '0' or placar_fora != '0':
            print('Gol detectado. Pausando para validação...')
            time.sleep(120)
            if placar_casa != '0' or placar_fora != '0':
                return True
            else:
                return False

        else:
            return False

    except TimeoutException:
        print('Erro ao capturar informações do placar: Elemento não encontrado.')
        return False

    except Exception as e:
        print(f'Erro ao verificar o status do mercado: {e}')
        return False


def busca_odds(driver):
    time.sleep(2)
    try:
        over_05_ht = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//div[@role='tabpanel']//div[2]//div[1]//div[1]//div[2]//div[1]//div[2]//div[1]//div[1]//div[1]//div[2]//div[2]//div[1]//button[1]")
            )
        ).text
        under_05_ht = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//div[@role='tabpanel']//div[2]//div[1]//div[1]//div[2]//div[1]//div[2]//div[1]//div[1]//div[1]//div[2]//div[3]//div[1]//button[1]")
            )
        ).text
        
        if over_05_ht == '-' or under_05_ht == '-':
            print('Mercado suspenso, odds não disponíveis.')
            return None, None
        # Verificar se os valores obtidos são números válidos
        try:
            odd_over = float(over_05_ht)
            odd_under = float(under_05_ht)
            return odd_over, odd_under
        except ValueError:
            print(f'Erro ao converter os valores das odds. Over:{odd_over}, Under: {odd_under}')
            return None, None
    except TimeoutException:
        print("Erro ao buscar as odds: Elemento não encontrado.")
        return None, None


def monitora_odd(driver):
    print('Iniciando monitoramento...')
    while True:
        try:
            tempo_valido, minutos = verifica_tempo(driver)

            if verifica_placar(driver) or tempo_valido:
                print('Encerrando monitoramento.')
                return False, None

            over, under = busca_odds(driver)

            if over is None or under is None:
                print('Não foi possível obter as odds. Continuando monitoramento...')
                time.sleep(60)
                continue

            print(f'Over: {over} | Under: {under} | Tempo: {minutos} min.')

            if over >= ODD_ALVO:
                print(f'Odd Over 0.5 HT alcançada: {over} | Tempo de jogo: {minutos} min')
                xpath = "//div[@role='tabpanel']//div[2]//div[1]//div[1]//div[2]//div[1]//div[2]//div[1]//div[1]//div[1]//div[2]//div[2]//div[1]//button[1]"
                return True, xpath

            if under <= ODD_ALVO:
                print(f'Odd Under 0.5 HT alcançada: {under} | Tempo de jogo: {minutos} min')
                xpath = "//div[@role='tabpanel']//div[2]//div[1]//div[1]//div[2]//div[1]//div[2]//div[1]//div[1]//div[1]//div[2]//div[3]//div[1]//button[1]"
                return True, xpath

            time.sleep(30)

        except TimeoutException as e:
            print('Erro de tempo de espera:', e)

        except NoSuchElementException as e:
            print('Elemento não encontrado:', e)

        except Exception as e:
            print('Erro inesperado:', e)


def verifica_saldo(driver):
    try:
        saldo = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//tr[@rel='main-wallet']//td[@class='ssc-wla']"))
        ).text.strip()
        
        valor_saldo = float(saldo.replace('R$', ''))

        if valor_saldo >= VALOR_BET:
            print("Saldo suficiente para realizar a aposta.")
            return True
        else:
            print('Saldo insuficiente. Encerrando monitoramento.')
            return False

    except Exception as e:
        print("Erro ao verificar saldo:", e)
        return False


def faz_bet(driver, xpath):
    try:
        if not verifica_saldo(driver):
            return

        # Botão da odd
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        ).click()

        # Botão termos da Betfair
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[normalize-space()='Aceitar']"))
        ).click()

        # Campo onde preenche o valor da bet
        bet_input = driver.find_element(By.CLASS_NAME, '_2Sn4h')
        bet_input.clear()
        bet_input.send_keys(str(VALOR_BET))

        # Botão de fazer a bet
        bet_button = driver.find_element(By.CLASS_NAME, '_3DCMk')
        bet_button.click()
        print(f'Aposta de {VALOR_BET} realizada com sucesso!')

    except Exception as e:
        print('Erro ao realizar a aposta:', e)


def main():
    # Configuração de opções do Chrome
    options = Options()
    options.add_argument('--disable-gpu')  # Desabilita GPU
    options.add_argument('--disable-extensions')  # Desativa extensões
    options.add_argument('--start-maximized')  # Maximiza a janela

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(URL)
        aceita_cookies(driver)
        email, senha = carrega_credenciais()
        login(driver, email, senha)
        time.sleep(3)
        input('Selecione o jogo manualmente e pressione Enter...')

        # botão aba gols
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//span[normalize-space()='Gols']"))).click()

        # botão minimiza aba 'Mais/menos gols'
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "(//div[@class='_9nVCd _2Vnv_']//div[@class='CJaOy'])[2]"))
        ).click()

        odd_valida, xpath = monitora_odd(driver)

        if odd_valida:
            faz_bet(driver, xpath)

    except Exception as e:
        print('Erro:', e)

    finally:
        time.sleep(5)
        driver.quit()


if __name__ == '__main__':
    main()
