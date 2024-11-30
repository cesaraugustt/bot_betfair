from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
import time
import os
import re


URL = 'https://www.betfair.com/'
ODD_ALVO = 5
TEMPO_MAX = 45
VALOR_BET = 0.58


def aceita_cookies(driver):
    try:
        time.sleep(2)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.ID, 'onetrust-reject-all-handler'))).click()
        print('Cookies aceitos.')

    except Exception as e:
        print('Erro ao aceitar cookies ou botão não encontrado:', e)


def login(driver):
    try:
        email = os.getenv('EMAIL')
        senha = os.getenv('SENHA')
        if not email or not senha:
            print('Credenciais de login não configuradas.')

        driver.find_element(By.ID, 'ssc-liu').send_keys(email)
        driver.find_element(By.ID, 'ssc-lipw').send_keys(senha)
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'ssc-lis'))).click()
        print('Login realizado.')

    except Exception as e:
        print('Erro durante o login:', e)


def verifica_tempo(driver):
    try:
        tempo_elemento = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, '_2MTBZ')))
        minutos = int(tempo_elemento.text.replace("'", ""))

        if minutos > TEMPO_MAX:
            print('Tempo máximo atingido')
            return True, minutos

        else:
            return False, minutos

    except NoSuchElementException:
        print('Elemento de tempo não encontrado.')
        return False

    except ValueError as e:
        print(f'Erro ao converter tempo: {e}')
        return False


def verifica_mercado(driver):
    try:
        placar_casa = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='_3zclL']//div[1]")))
        placar_casa_text = placar_casa.text

        placar_fora = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='_2v7CY PuNpm']//div[2]")))
        placar_fora_text = placar_fora.text

        print(f'Placar: {placar_casa_text} x {placar_fora_text}')

        if placar_casa_text != '0' or placar_fora_text != '0':
            print('Mercado fechado.')
            return True

        else:
            return False

    except TimeoutException:
        return False

    except Exception as e:
        print(f'Erro ao verificar o status do mercado: {e}')
        return False


def monitora_odd(driver):
    print('Iniciando monitoramento...')

    while True:
        try:
            tempo_valido, minutos = verifica_tempo(driver)

            if verifica_mercado(driver) or tempo_valido:
                print('Encerrando monitoramento.')
                return False

            over_05_ht = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//div[@role='tabpanel']//div[2]//div[1]//div[1]//div[2]//div[1]//div[2]//div[1]//div[1]//div[1]//div[2]//div[2]//div[1]//button[1]")
                )
            )

            odd_over_05_ht = over_05_ht.text

            under_05_ht = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//div[@role='tabpanel']//div[2]//div[1]//div[1]//div[2]//div[1]//div[2]//div[1]//div[1]//div[1]//div[2]//div[3]//div[1]//button[1]")
                )
            )

            odd_under_05_ht = under_05_ht.text

            # Verificar se os valores obtidos são números válidos
            try:
                odd_over_05_ht = float(odd_over_05_ht)
                odd_under_05_ht = float(odd_under_05_ht)
            except ValueError:
                print(f'Erro ao converter os valores das odds. Over:'
                      f'{odd_over_05_ht}, Under: {odd_under_05_ht}')
                time.sleep(15)
                continue

            print(f'Over: {odd_over_05_ht} | Under: '
                  f'{odd_under_05_ht} | Tempo: {minutos} min.')

            if odd_over_05_ht >= ODD_ALVO:
                print(f'Odd desejada alcançada: '
                      f'{odd_over_05_ht} | Tempo de jogo: {minutos} min')
                xpath = "//div[@role='tabpanel']//div[2]//div[1]//div[1]//div[2]//div[1]//div[2]//div[1]//div[1]//div[1]//div[2]//div[2]//div[1]//button[1]"
                return True, xpath

            if odd_under_05_ht >= ODD_ALVO:
                print(f'Odd desejada alcançada:'
                      f'{odd_under_05_ht} | Tempo de jogo: {minutos} min')
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
                (By.CLASS_NAME, "//tr[@rel='main-wallet']//td[@class='ssc-wla']"))
        )

        if saldo >= VALOR_BET:
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

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        ).click()

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[normalize-space()='Aceitar']"))
        ).click()

        bet_input = driver.find_element(By.CLASS_NAME, '_2Sn4h')
        bet_input.clear()
        bet_input.send_keys(str(VALOR_BET))

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
    load_dotenv()

    try:
        driver.get(URL)
        aceita_cookies(driver)
        login(driver)

        time.sleep(1)

        print('Selecione manualmente o jogo.')
        input('Pressione Enter após selecionar o mercado para iniciar o monitoramento...')

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
