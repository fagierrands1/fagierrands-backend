@echo off
REM M-Pesa Testing Script
REM This script provides an interactive menu to run different M-Pesa tests

setlocal enabledelayedexpansion
set SCRIPT_DIR=%~dp0

:menu
cls
echo.
echo ================================================================================
echo                    M-PESA DARAJA API TESTING SUITE
echo ================================================================================
echo.
echo Select a test option:
echo.
echo   1. Run Quick Manual Tests (Recommended for first run)
echo   2. Run All M-Pesa Tests (Django Test Suite)
echo   3. Run M-Pesa Service Tests Only
echo   4. Run M-Pesa API View Tests Only
echo   5. Run M-Pesa Integration Tests Only
echo   6. Run Specific Test
echo   7. View Testing Guide
echo   8. Exit
echo.

set /p choice="Enter your choice (1-8): "

if "%choice%"=="1" goto quick_test
if "%choice%"=="2" goto all_tests
if "%choice%"=="3" goto service_tests
if "%choice%"=="4" goto view_tests
if "%choice%"=="5" goto integration_tests
if "%choice%"=="6" goto specific_test
if "%choice%"=="7" goto view_guide
if "%choice%"=="8" goto exit_script

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto menu

:quick_test
cls
echo.
echo Running Quick M-Pesa Tests...
echo.
python quick_test_mpesa.py
pause
goto menu

:all_tests
cls
echo.
echo Running All M-Pesa Tests...
echo.
python manage.py test test_mpesa_comprehensive -v 2
pause
goto menu

:service_tests
cls
echo.
echo Running M-Pesa Service Tests...
echo.
python manage.py test test_mpesa_comprehensive.MpesaServiceTestCase -v 2
pause
goto menu

:view_tests
cls
echo.
echo Running M-Pesa API View Tests...
echo.
python manage.py test test_mpesa_comprehensive.MpesaAPIViewsTestCase -v 2
pause
goto menu

:integration_tests
cls
echo.
echo Running M-Pesa Integration Tests...
echo.
python manage.py test test_mpesa_comprehensive.MpesaIntegrationTestCase -v 2
pause
goto menu

:specific_test
cls
echo.
echo Available Specific Tests:
echo.
echo   1. test_get_access_token
echo   2. test_stk_push_with_valid_phone
echo   3. test_stk_push_different_amounts
echo   4. test_stk_query
echo   5. test_account_balance
echo   6. test_b2c_payment
echo   7. test_b2b_payment
echo   8. test_transaction_status
echo   9. test_dynamic_qr_code
echo   10. test_reversal
echo   11. test_phone_number_formatting
echo   12. test_phone_number_validation
echo   13. test_complete_payment_flow
echo.

set /p test_choice="Enter test number or full test name: "

if "%test_choice%"=="1" (
    set test_name=test_get_access_token
) else if "%test_choice%"=="2" (
    set test_name=test_stk_push_with_valid_phone
) else if "%test_choice%"=="3" (
    set test_name=test_stk_push_different_amounts
) else if "%test_choice%"=="4" (
    set test_name=test_stk_query
) else if "%test_choice%"=="5" (
    set test_name=test_account_balance
) else if "%test_choice%"=="6" (
    set test_name=test_b2c_payment
) else if "%test_choice%"=="7" (
    set test_name=test_b2b_payment
) else if "%test_choice%"=="8" (
    set test_name=test_transaction_status
) else if "%test_choice%"=="9" (
    set test_name=test_dynamic_qr_code
) else if "%test_choice%"=="10" (
    set test_name=test_reversal
) else if "%test_choice%"=="11" (
    set test_name=test_phone_number_formatting
) else if "%test_choice%"=="12" (
    set test_name=test_phone_number_validation
) else if "%test_choice%"=="13" (
    set test_name=test_complete_payment_flow
) else (
    set test_name=%test_choice%
)

cls
echo.
echo Running Test: !test_name!
echo.
python manage.py test test_mpesa_comprehensive.MpesaServiceTestCase.!test_name! -v 2
pause
goto menu

:view_guide
cls
echo.
echo Opening M-Pesa Testing Guide...
echo.
if exist MPESA_TESTING_GUIDE.md (
    more MPESA_TESTING_GUIDE.md
) else (
    echo Testing guide not found.
)
pause
goto menu

:exit_script
echo.
echo Goodbye!
echo.
exit /b 0